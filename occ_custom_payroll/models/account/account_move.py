# -*- coding: utf-8 -*-
# Native Python modules
from contextlib import contextmanager

# Local python modules

# Custom python modules

# Odoo modules
from odoo import models, fields, api, _
from odoo.tools.translate import _
from odoo.exceptions import UserError, ValidationError


class account_move(models.Model):
    _inherit = "account.move"

    @contextmanager
    def _check_balanced(self, container):
        """Assert the move is fully balanced debit = credit.
        An error is raised if it's not the case.
        """
        moves = self.filtered(lambda move: move.line_ids)
        if not moves:
            yield
            return

        # /!\ As this method is called in create / write, we can't make the assumption the computed stored fields
        # are already done. Then, this query MUST NOT depend of computed stored fields (e.g. balance).
        # It happens as the ORM makes the create with the 'no_recompute' statement.
        self.env["account.move.line"].flush(["debit", "credit", "move_id"])
        self.env["account.move"].flush(["journal_id"])
        self._cr.execute(
            """
			SELECT line.move_id, ROUND(SUM(debit - credit), currency.decimal_places)
			FROM account_move_line line
			JOIN account_move move ON move.id = line.move_id
			JOIN account_journal journal ON journal.id = move.journal_id
			JOIN res_company company ON company.id = journal.company_id
			JOIN res_currency currency ON currency.id = company.currency_id
			WHERE line.move_id IN %s
			GROUP BY line.move_id, currency.decimal_places
			HAVING ROUND(SUM(debit - credit), currency.decimal_places) != 0.0;
		""",
            [tuple(self.ids)],
        )

        query_res = self._cr.fetchall()
        if query_res:
            ids = [res[0] for res in query_res]
            sums = [res[1] for res in query_res]
            if self.name[0:3] != "PYJ":
                raise UserError(
                    _(
                        "Cannot create unbalanced journal entry. Ids: %s\nDifferences debit - credit: %s"
                    )
                    % (ids, sums)
                )
        yield

class HRAccountMoveLine(models.Model):
    _inherit = "account.move.line"

    analytic_account_id = fields.Many2one(
        comodel_name="account.analytic.account",
        string="Analytic Account",
        copy=False,
        check_company=True,
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]"
    )
# -*- coding: utf-8 -*-
# Native Python modules
from datetime import datetime, date, timedelta

# Local python modules

# Custom python modules

# Odoo modules
from odoo import models, fields, api, _
from odoo.tools.translate import _
from odoo.tools import float_round
from odoo.exceptions import UserError, ValidationError
import odoo.addons.decimal_precision as dp

class exhr_payslip_nontaxable(models.Model):
    _name = "exhr.payslip.nontaxable"

    name_id = fields.Many2one("nontaxable.type", string="Description", index=True)
    ref = fields.Char(string="Reference")
    amount_total = fields.Monetary(string="Amount", store=True)
    pay_type = fields.Selection(
        [("earnings", "Earnings"), ("deductions", "Deductions")],
        string="Type",
        default="earnings",
    )
    payslip_id = fields.Many2one(
        "exhr.payslip", "nontaxable_line_ids", store=True, ondelete="cascade", index=True
    )
    currency_id = fields.Many2one(
        "res.currency", related="payslip_id.currency_id", store=True, related_sudo=False
    )
    company_currency_id = fields.Many2one(
        "res.currency",
        related="payslip_id.company_currency_id",
        readonly=True,
        related_sudo=False,
    )

    taxable = fields.Boolean("Taxable")
    loan_id = fields.Many2one("loan.monitoring")

    gl_account_id = fields.Many2one("account.account", "GL Account")

    # loan_name = fields.Many2one('loan.monitoring', 'Loan Name')
    new_loan_name = fields.Char(string="Loan Name")

    @api.onchange("amount_total", "pay_type")
    def onchange_amount_total(self):

        if self.pay_type == "earnings":
            if self.amount_total < 0:
                # make it positive
                self.amount_total = self.amount_total * -1

        elif self.pay_type == "deductions":
            if self.amount_total > 0:
                # make it negative
                self.amount_total = self.amount_total * -1

    def action_populate_gl_account_id(self):
        nontaxable_list = self.env["exhr.payslip.nontaxable"].search(
            [("gl_account_id", "=", False)]
        )
        for rec in nontaxable_list:
            if not rec.gl_account_id:
                if rec.loan_id:
                    rec.gl_account_id = rec.loan_id.gl_account.id
                else:
                    rec.gl_account_id = (
                        rec.payslip_id.employee_id.accounting_tag_id.default_others_account_id.id
                    )

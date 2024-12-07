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

class exhr_payslip_deductions(models.Model):
    _name = "exhr.payslip.deductions"

    # name = fields.Char(string="Deductions")#many2one
    name_id = fields.Many2one("deduction.type", string="Deductions", index=True)
    # amount = fields.Float(string="Amount", digits=(5, 2))
    amount_total = fields.Monetary(string="Amount", store=True)
    no_day_hrs_disp = fields.Char(string="Hrs/Days")
    payslip_id = fields.Many2one(
        "exhr.payslip", "deductions_line_ids", store=True, ondelete="cascade", index=True
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

    # other fields for history
    personal_contri = fields.Float(
        string="Amount Personal Share", help="HDMF/PHIC - Employee Share"
    )
    employer_contri = fields.Float(
        string="Amount Employer Share", help="HDMF/PHIC - Employer Share"
    )

    total_ss_contri = fields.Float(
        string="Total (SS Contri.)", help="SSS - Total (SS Contribution)"
    )
    er_ec_contri = fields.Float(string="EC Contri.", help="SSS - EC Contribtion (ER)")

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


class exhr_payslip_earnings(models.Model):
    _name = "exhr.payslip.earnings"

    # name = fields.Char(string="Earnings")#many2one
    name_id = fields.Many2one("earnings.type", string="Earnings", index=True)
    date = fields.Char(string="Date")
    no_day_hrs = fields.Float(string="No. of Hrs", digits=(5, 2))
    no_day_hrs_disp = fields.Char(string="Hrs/Days")
    amt_per_day_hrs = fields.Float(string="Amt. per Hr", digits=(5, 2))
    amount_subtotal = fields.Monetary(string="Sub Total Amount", store=True)

    payslip_id = fields.Many2one(
        "exhr.payslip", "earnings_line_ids", store=True, ondelete="cascade", index=True
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

    @api.onchange("no_day_hrs", "amt_per_day_hrs")
    def onchange_compute_amt_subtotal(self):
        self.amount_subtotal = self.no_day_hrs * self.amt_per_day_hrs

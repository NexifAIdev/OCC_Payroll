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

class sss_contribution(models.Model):
    _name = "sss.contribution.line"

    payslip_id = fields.Many2one(
        "exhr.payslip", string="Payslip", store=True, index=True, ondelete="cascade"
    )
    date = fields.Date("Date")
    ee_regular_amount = fields.Float("EE (Regular SS)")
    er_regular_amount = fields.Float("ER (Regular SS)")
    ee_ec_amount = fields.Float("EE (EC)")
    er_ec_amount = fields.Float("ER (EC)")
    ee_mpf_amount = fields.Float("EE (MPF)")
    er_mpf_amount = fields.Float("ER (MPF)")
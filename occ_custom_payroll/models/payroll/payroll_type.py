# -*- coding: utf-8 -*-
# Native Python modules

# Local python modules

# Custom python modules

# Odoo modules
from odoo import models, fields, api, _
from odoo.tools.translate import _
from odoo.exceptions import UserError, ValidationError


class PayrollType(models.Model):
    _name = "payroll.type"
    _description = "Payroll Type"
    _order = "sequence, id"

    name = fields.Char(string="Payroll Type", required=True)
    sequence = fields.Integer(
        help="Gives the sequence when displaying a list of Payroll Type.", default=10
    )

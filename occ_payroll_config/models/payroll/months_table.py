# -*- coding: utf-8 -*-
# Native Python modules

# Local python modules

# Custom python modules

# Odoo modules
from odoo import models, fields, api, _
from odoo.tools.translate import _
from odoo.exceptions import UserError, ValidationError

class MonthsTable(models.Model):
    _name = "months.table"
    _snakecased_name = "months_table"
    _model_path_name = "occ_payroll.model_months_table"
    _description = "Months Table"
    
    name = fields.Char(
        string="Type",
        default=False,
        required=True,
    )
    
    short_name = fields.Char(
        string="Short Name",
        default=False,
        required=True,
    )
    
    ordinal_number = fields.Integer(
        string="Number",
        default=False,
        required=True,
    )
    
    cardinal_number = fields.Integer(
        string="Number",
        default=False,
        required=True,
    )
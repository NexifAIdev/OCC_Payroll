# -*- coding: utf-8 -*-
# Native Python modules

# Local python modules

# Custom python modules

# Odoo modules
from odoo import models, fields, api, _
from odoo.tools.translate import _
from odoo.exceptions import UserError, ValidationError


class DaysTable(models.Model):
    _name = "days.table"
    _snakecased_name = "days_table"
    _model_path_name = "occ_payroll.model_days_table"
    _description = "Days Table"

    name = fields.Char(
        string="Type",
        default=False,
        required=True,
    )

    ordinal_number = fields.Integer(
        string="Number",
        default=False,
        required=True,
    )

    cardinal_number = fields.Char(
        string="Cardinal Number",
        default=False,
        required=True,
    )

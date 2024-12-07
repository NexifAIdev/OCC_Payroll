# -*- coding: utf-8 -*-
# Native Python modules
import calendar

# Local python modules

# Custom python modules

# Odoo modules
from odoo import models, fields, api, _
from odoo.tools.translate import _
from odoo.exceptions import UserError, ValidationError


class PHICTable(models.Model):
    _name = "phic.table"
    _snakecase_name = "phic_table"
    _model_path_name = "occ_payroll.model_phic_table"
    _description = "PHIC Table"
    
    name = fields.Char(
        string="Name",
        default=False,
        required=True,
    )
    
    year_range = fields.Char(
        string="Year",
        default="2000",
        required=True,
    )
    
    monthly_basic_salary = fields.Char(
        string="Monthly Basic Salary",
        default=False,
        required=True,
    )
    
    premium_rate = fields.Char(
        string="Premium Rate",
        default=False,
        required=True,
    )
    
    monthly_premium = fields.Char(
        string="Monthly Premium",
        default=False,
        required=True,
    )
    
    active = fields.Boolean(
        string="Active",
        default=True,
    )
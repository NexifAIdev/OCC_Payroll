# -*- coding: utf-8 -*-
# Native Python modules
import calendar

# Local python modules

# Custom python modules

# Odoo modules
from odoo import models, fields, api, _
from odoo.tools.translate import _
from odoo.exceptions import UserError, ValidationError


class SalaryAdjustmentConfig(models.Model):
    _name = 'salary.adjustment.config'
    _snakecased_name = 'salary_adjustment_config'
    _model_path_name = 'occ_payroll_config.salary_adjustment_config'
    _description = 'Salary Adjustment Config'
    
    name = fields.Char(
        string='Name', 
        required=True
    )
    
    description = fields.Char(
        string='Description', 
        required=True
    )
    
    computation = fields.Char(
        string='Computation', 
        required=True
    )
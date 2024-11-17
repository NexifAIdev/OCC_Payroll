# -*- coding: utf-8 -*-
# Native Python modules
import calendar

# Local python modules

# Custom python modules

# Odoo modules
from odoo import models, fields, api, _
from odoo.tools.translate import _
from odoo.exceptions import UserError, ValidationError

class HDMFTable(models.Model):
    _name = "hmdf.table"
    _snakecase_name = "hdmf_table"
    _model_path_name = "occ_payroll.model_hdmf_table"
    _description = "HDMF Table"
    
    name = fields.Char(
        string="Name",
        default=False,
        required=True,
    )
    
    monthly_salary = fields.Char(
        string="Monthly Basic Salary",
        default=False,
        required=True,
    )
    
    amount_type = fields.Selection(
        string="Amount Type",
        selection=[
            ("percentage", "Percentage"), 
            ("fixed_amount", "Fixed Amount")
        ],
        default="percentage",
    )
    
    employers_contribution_rate = fields.Float(
        string="Premium Rate",
        default=False,
        required=True,
    )
    
    employees_contribution_rate = fields.Float(
        string="Premium Rate",
        default=False,
        required=True,
    )
    
    total_contribution = fields.Float(
        string="Total Contribution",
        default=False,
    )
    
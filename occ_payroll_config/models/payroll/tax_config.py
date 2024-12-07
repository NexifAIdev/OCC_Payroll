# -*- coding: utf-8 -*-
# Native Python modules
import calendar

# Local python modules

# Custom python modules

# Odoo modules
from odoo import models, fields, api, _
from odoo.tools.translate import _
from odoo.exceptions import UserError, ValidationError

class RevisedWithholdingTaxTable(models.Model):
    _name = "revised.withholding.tax.table"
    _snakecased_name = "revised_withholding_tax_table"
    _model_path_name = "occ_payroll_config.revised_withholding_tax_table"
    _description = "Revised Withholding Tax Table"
    
    name = fields.Char(
        string="Name",
        default=False,
        required=True,
    )
    
    description = fields.Char(
        string="Description",
        default=False,
        required=True,
    )
    
    effective_date = fields.Date(
        string="Effective Date",
        default=False,
        required=True,
    )
    
    time_period = fields.Selection(
        string="Time Period",
        selection=[
            ("daily", "Daily"), 
            ("weekly", "Weekly"), 
            ("semi_monthly", "Semi-Monthly"),
            ("monthly", "Monthly"), 
            ("quarterly", "Quarterly"), 
            ("yearly", "Yearly"),
        ],
        default="monthly",
        required=True,
    )
    
    level = fields.Integer(
        string="Level",
        default=False,
        required=True,
    )
    
    compensation_range = fields.Char(
        string="Compensation Range",
        default=False,
        required=True,
    )
    
    tax_rate = fields.Char(
        string="Tax Rate",
        default=False,
        required=True,
    )
    
    currency = fields.Many2one(
        string="Currency",
        comodel_name="res.currency",
        default=False,
        required=True,
    )
    
    active = fields.Boolean(
        string="Active",
        default=True,
    )
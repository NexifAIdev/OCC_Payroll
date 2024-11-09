# -*- coding: utf-8 -*-
# Native Python modules

# Local python modules

# Custom python modules

# Odoo modules
from odoo import models, fields, api, _
from odoo.tools.translate import _
from odoo.exceptions import UserError, ValidationError

class HolidaysConfiguration(models.Model):
    _name = "hr.holidays.configuration"
    _snakecased_name = "hr_holidays_configuration"
    _model_path_name = "occ_payroll.model_hr_holidays_configuration"
    _description = "Holidays Configuration"
    
    name = fields.Char(
        string="Type",
        default=False,
        required=True,
    )
    
    code = fields.Char(
        string="Code",
        default=False,
        required=True,
    )
    
    description = fields.Char(
        string="Description",
        default=False,
        required=True,
    )
    
    active = fields.Boolean(
        string="Active",
        default=True,
    )
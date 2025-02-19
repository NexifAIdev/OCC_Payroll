# -*- coding: utf-8 -*-
# Native Python modules

# Local python modules

# Custom python modules

# Odoo modules
from odoo import models, fields, api, _
from odoo.tools.translate import _
from odoo.exceptions import UserError, ValidationError


class EmployeeTypes(models.Model):
    _name = "hr.employee.types"
    _snakecased_name = "hr_employee_types"
    _model_path_name = "occ_payroll.model_hr_employee_types"
    _description = "Employee Types"

    name = fields.Char(
        string="Types",
        default=False,
        required=True,
    )
    
    for_payroll = fields.Boolean(
        string="For Payroll",
        default=True,
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

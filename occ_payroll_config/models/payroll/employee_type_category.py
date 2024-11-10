# -*- coding: utf-8 -*-
# Native Python modules

# Local python modules

# Custom python modules

# Odoo modules
from odoo import models, fields, api, _
from odoo.tools.translate import _
from odoo.exceptions import UserError, ValidationError

class EmployeeTypesCategory(models.Model):
    _name = "hr.employee.types.category"
    _snakecased_name = "hr_employee_types_category"
    _model_path_name = "occ_payroll.model_hr_employee_types_category"
    _description = "Employee Types Category"
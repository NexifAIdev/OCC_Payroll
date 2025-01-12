# -*- coding: utf-8 -*-
# Native Python modules

# Local python modules

# Custom python modules

# Odoo modules
from odoo import models, fields, api, _
from odoo.tools.translate import _
from odoo.exceptions import UserError, ValidationError


class EmployeePosition(models.Model):
    _name = "employee.position"
    _description = "Employee Position"
    _order = "started_date desc"

    position = fields.Char(string="Position")
    company = fields.Char(string="Company")
    level = fields.Char(string="Level/Department")
    started_date = fields.Date(string="Started")
    ended_date = fields.Date(string="Ended")
    employee_id = fields.Many2one("hr.employee", string="Employee", ondelete="cascade")

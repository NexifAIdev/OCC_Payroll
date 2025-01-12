# -*- coding: utf-8 -*-
# Native Python modules

# Local python modules

# Custom python modules

# Odoo modules
from odoo import models, fields, api, _
from odoo.tools.translate import _
from odoo.exceptions import UserError, ValidationError


class EmployeeDependents(models.Model):
    _name = "employee.dependents"
    _description = "Employee Dependents"
    _order = "birthdate desc"

    lname = fields.Char(string="Last Name")
    fname = fields.Char(string="First Name")
    mname = fields.Char(string="Middle Name")
    relationship_id = fields.Many2one("hr.relationship", string="Relationship")
    birthdate = fields.Date(string="Birthday")
    school_level = fields.Char(string="Level/School")
    employee_id = fields.Many2one("hr.employee", string="Employee", ondelete="cascade")

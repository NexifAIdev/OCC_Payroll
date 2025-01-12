# -*- coding: utf-8 -*-
# Native Python modules

# Local python modules

# Custom python modules

# Odoo modules
from odoo import models, fields, api, _
from odoo.tools.translate import _
from odoo.exceptions import UserError, ValidationError


class EmployeeIncident(models.Model):
    _name = "employee.incident"
    _description = "Employee Incident Report"
    _order = "date desc"

    # name = fields.Char(string='Subject', required=True)
    date = fields.Date(required=True)
    disciple_id = fields.Many2one("nature.discipline", string="Nature of Discipline")
    details = fields.Text(string="Details", required=True)
    penalty_id = fields.Many2one("penalty.sanction", string="Penalty/Sanction")
    attachment = fields.Binary(string="Attached file of employee's Explanation Letter")
    employee_id = fields.Many2one("hr.employee", string="Employee", ondelete="cascade")

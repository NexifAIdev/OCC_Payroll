# -*- coding: utf-8 -*-
# Native Python modules

# Local python modules

# Custom python modules

# Odoo modules
from odoo import models, fields, api, _
from odoo.tools.translate import _
from odoo.exceptions import UserError, ValidationError


class HrEmployeeSeminar(models.Model):
    _name = "hr.employee.seminar"
    _order = "seminar_start desc"

    employee_id = fields.Many2one(
        comodel_name="hr.employee", string="Employee ID", ondelete="cascade"
    )

    seminar_title = fields.Char(
        string="Seminar Title",
    )
    venue = fields.Char(
        string="Venue",
    )
    speaker = fields.Char(
        string="Speaker",
    )
    seminar_start = fields.Date(
        string="Start Date",
    )
    seminar_end = fields.Date(
        string="End Date",
    )

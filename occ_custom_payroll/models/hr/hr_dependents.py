# -*- coding: utf-8 -*-
# Native Python modules

# Local python modules

# Custom python modules

# Odoo modules
from odoo import models, fields, api, _
from odoo.tools.translate import _
from odoo.exceptions import UserError, ValidationError

class Hrdependents(models.Model):
    _name = "hr.dependents"
    _order = "d_birthday desc"

    employee_id = fields.Many2one(
        comodel_name="hr.employee",
        string="Employee ID",
        ondelete="cascade",
    )

    d_first = fields.Char(
        string="First Name",
    )
    d_last = fields.Char(
        string="Last Name",
    )
    d_rel = fields.Char(
        string="Relationship",
    )
    d_birthday = fields.Date(
        string="Date of Birth",
    )
    school_level = fields.Char(
        string="Level/School",
    )
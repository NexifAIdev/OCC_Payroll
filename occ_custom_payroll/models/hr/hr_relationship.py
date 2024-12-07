# -*- coding: utf-8 -*-
# Native Python modules

# Local python modules

# Custom python modules

# Odoo modules
from odoo import models, fields, api, _
from odoo.tools.translate import _
from odoo.exceptions import UserError, ValidationError

class HrRelationship(models.Model):
    _name = "hr.relationship"
    _description = "Employee Relationship"

    name = fields.Char(
        string="Relationship",
    )
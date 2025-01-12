# -*- coding: utf-8 -*-
# Native Python modules

# Local python modules

# Custom python modules

# Odoo modules
from odoo import models, fields, api, _
from odoo.tools.translate import _
from odoo.exceptions import UserError, ValidationError


class HrDegree(models.Model):
    _name = "hr.degree"
    _order = "name asc"

    name = fields.Char(
        string="Degree Obtained",
    )

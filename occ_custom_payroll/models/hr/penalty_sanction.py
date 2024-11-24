# -*- coding: utf-8 -*-
# Native Python modules

# Local python modules

# Custom python modules

# Odoo modules
from odoo import models, fields, api, _
from odoo.tools.translate import _
from odoo.exceptions import UserError, ValidationError

class PenaltySanction(models.Model):
    _name = "penalty.sanction"
    _description = "Penalty/Sanction"

    name = fields.Char("Name")
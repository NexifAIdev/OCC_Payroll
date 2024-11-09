# -*- coding: utf-8 -*-
# Native Python modules

# Local python modules

# Custom python modules

# Odoo modules
from odoo import models, fields, api, _
from odoo.tools.translate import _
from odoo.exceptions import UserError, ValidationError

class NontaxableType(models.Model):
    _name = "nontaxable.type"
    _snakecased_name = "nontaxable_type"
    _model_path_name = "occ_payroll.model_nontaxable_type"
    _description = "Nontaxable Type"
    
    name = fields.Char(
        string="Type",
        default=False,
        required=True,
    )
    
    sequence = fields.Integer()
    
    description = fields.Char(
        string="Description",
        default=False,
        required=True,
    )
    
    active = fields.Boolean(
        string="Active",
        default=True,
    )
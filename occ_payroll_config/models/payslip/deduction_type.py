# -*- coding: utf-8 -*-
# Native Python modules

# Local python modules

# Custom python modules

# Odoo modules
from odoo import models, fields, api, _
from odoo.tools.translate import _
from odoo.exceptions import UserError, ValidationError


class DeductionType(models.Model):
    _name = "deduction.type"
    _snakecased_name = "deduction_type"
    _model_path_name = "occ_payroll.model_deduction_type"
    _description = "Deduction Type"

    name = fields.Char(
        string="Name of Deduction",
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

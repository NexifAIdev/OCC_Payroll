# -*- coding: utf-8 -*-
# Native Python modules

# Local python modules

# Custom python modules

# Odoo modules
from odoo import models, fields, api, _
from odoo.tools.translate import _
from odoo.exceptions import UserError, ValidationError


class EarningsType(models.Model):
    _name = "earnings.type"
    _snakecased_name = "earnings_type"
    _model_path_name = "occ_payroll.model_earnings_type"
    _description = "Earnings Type"

    name = fields.Char(
        string="Name of Earning",
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

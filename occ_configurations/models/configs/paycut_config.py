# -*- coding: utf-8 -*-
# Native Python modules
import calendar

# Local python modules

# Custom python modules

# Odoo modules
from odoo import models, fields, api, _
from odoo.tools.translate import _
from odoo.exceptions import UserError, ValidationError


class PaycutConfiguration(models.Model):
    _name = "paycut.configuration"
    _snakecased_name = "paycut_configuration"
    _model_path_name = "occ_configurations.model_paycut_configuration"
    _description = "Paycut Configuration"

    name = fields.Char(
        string="Type",
        default=False,
        required=True,
    )

    start_day = fields.Integer(
        string="Start Day",
        default=False,
        required=True,
    )

    end_day = fields.Integer(
        string="End Day",
        default=False,
        required=True,
    )

    description = fields.Char(
        string="Description",
        default=False,
        required=True,
    )

    active = fields.Boolean(
        string="Active",
        default=True,
    )

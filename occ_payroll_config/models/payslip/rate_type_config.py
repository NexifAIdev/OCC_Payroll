# -*- coding: utf-8 -*-
# Native Python modules

# Local python modules

# Custom python modules

# Odoo modules
from odoo import models, fields, api, _
from odoo.tools.translate import _
from odoo.exceptions import UserError, ValidationError


class RateTypeConfig(models.Model):
    _name = "rate.type.config"
    _snakecase_name = "rate_type_config"
    _model_path_name = "occ_payroll_config.model_rate_type_config"
    _description = "Rate Type Configuration"

    name = fields.Char(string="Name", required=True)
    active = fields.Boolean(string="Active", default=True)

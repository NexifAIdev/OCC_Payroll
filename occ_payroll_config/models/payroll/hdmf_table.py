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
    _model_path_name = "occ_payroll.model_paycut_configuration"
    _description = "Paycut Configuration"
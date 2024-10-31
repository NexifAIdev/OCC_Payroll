# -*- coding: utf-8 -*-
# Native Python modules

# Local python modules

# Custom python modules

# Odoo modules
from odoo import models, fields, api, tools, exceptions, _


class ResCityMunicipality(models.Model):
    _name = "res.citymun"
    _snakecased_name = "res_citymun"
    _model_path_name = "occ_configurations.model_res_citymun"
    _description = "City / Municipality"
    _order = "name"

    active = fields.Boolean("Active", default=True)
    name = fields.Char("City / Municipality")
    code = fields.Char("Code")
    province_id = fields.Many2one("res.province", "Region", ondelete="set null")

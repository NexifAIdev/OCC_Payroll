# -*- coding: utf-8 -*-
# Native Python modules

# Local python modules

# Custom python modules

# Odoo modules
from odoo import models, fields, api, tools, exceptions, _


class ResProvince(models.Model):
    _name = "res.province"
    _snakecased_name = "res_province"
    _model_path_name = "occ_configurations.model_res_province"
    _description = "Province"
    _order = "name"

    active = fields.Boolean("Active", default=True)
    name = fields.Char("Province")
    code = fields.Char("Code")
    region_id = fields.Many2one("res.region", "Region", ondelete="set null")

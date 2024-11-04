# -*- coding: utf-8 -*-
# Native Python modules

# Local python modules

# Custom python modules

# Odoo modules
from odoo import models, fields, api, tools, exceptions, _


class ResRegion(models.Model):
    _name = "res.region"
    _snakecased_name = "res_region"
    _model_path_name = "occ_configurations.model_res_region"
    _description = "Region"
    _order = "name"

    active = fields.Boolean("Active", default=True)
    name = fields.Char("Name")
    country_id = fields.Many2one("res.country", "Country", ondelete="set null")

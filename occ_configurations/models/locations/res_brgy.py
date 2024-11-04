# -*- coding: utf-8 -*-
# Native Python modules

# Local python modules

# Custom python modules

# Odoo modules
from odoo import models, fields, api, tools, exceptions, _


class ResBarangay(models.Model):
    _name = "res.brgy"
    _snakecased_name = "res_brgy"
    _model_path_name = "occ_configurations.model_res_brgy"
    _description = "Barangay"
    _order = "name"

    active = fields.Boolean("Active", default=True)
    name = fields.Char("Barangay")
    code = fields.Char("Code")
    citymun_id = fields.Many2one(
        "res.citymun", "City / Municipality", ondelete="set null"
    )

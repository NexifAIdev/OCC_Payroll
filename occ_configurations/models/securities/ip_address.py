# -*- coding: utf-8 -*-
# Native Python modules

# Local python modules

# Custom python modules

# Odoo modules
from odoo import models, fields, api, _
from odoo.tools.translate import _
from odoo.exceptions import UserError, ValidationError


class ResIPAddress(models.Model):
    _name = "res.ip.address"
    _snakecased_name = "res_ip_address"
    _model_path_name = "occ_configurations.model_res_ip_address"
    _description = "IP Addresses"

    name = fields.Char(
        string="Name",
        default=False,
        required=True,
    )

    name_compute = fields.Char(
        store=False,
        compute="_compute_name",
    )

    ip_address = fields.Char(
        string="IP Address",
        default=False,
        required=True,
    )

    active = fields.Boolean(
        string="Active", 
        default=True,
    )

    @api.depends("ip_address")
    def _compute_name(self):
        for rec in self:
            name = rec.name
            if rec.ip_address:
                name = f"{rec.ip_address}"
            rec.name = name
            rec.name_compute = name

    def unlink(self):
        for rec in self:
            rec.active = False

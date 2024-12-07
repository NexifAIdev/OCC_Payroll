# -*- coding: utf-8 -*-
# Native Python modules

# Local python modules

# Custom python modules

# Odoo modules
from odoo import models, fields, api, _
from odoo.tools.translate import _
from odoo.exceptions import UserError, ValidationError

print("created RateTypeList #####################################################")
class RateTypeList(models.Model):
    _name = "rate.type.list"
    _snakecased_name = "rate_type_list"
    _model_path_name = "occ_payroll_config.model_rate_type_list"
    _description = "Rate Type List"

    code = fields.Char(string="Code", required=True)
    name = fields.Char(string="Name", compute="_compute_name", store=True)
    description = fields.Char(
        string="Description", compute="_compute_description", store=True
    )
    rate_ids = fields.Many2many(
        comodel_name='rate.type.config',
        relation='rate_type_config_list_rel',  # Relation table name
        column1='list_id',                  # Column for this model
        column2='config_id',                    # Column for other model
        string='Rate Type Configs'
    )

    @api.depends("code", "rate_ids")
    def _compute_name(self):
        for rec in self:
            rate_names = ", ".join(rate.name for rate in rec.rate_ids)
            rec.name = f"{rec.code}: {rate_names}"

    @api.depends("rate_ids")
    def _compute_description(self):
        for rec in self:
            rec.description = ", ".join(rate.name for rate in rec.rate_ids)

# -*- coding: utf-8 -*-
# Native Python modules

# Local python modules

# Custom python modules

# Odoo modules
from odoo import models, fields, api, _
from odoo.tools.translate import _
from odoo.exceptions import UserError, ValidationError


class BonusesConfiguration(models.Model):
    _name = "bonuses.configuration"
    _snakecased_name = "bonuses_configuration"
    _model_path_name = "occ_payroll.model_bonuses_configuration"
    _description = "Bonuses Configuration"

    name = fields.Char(
        string="Type",
        default=False,
        required=True,
    )

    amount_type = fields.Selection(
        string="Amount Type",
        selection=[("percentage", "Percentage"), ("fixed_amount", "Fixed Amount")],
        default="fixed_amount",
    )

    condition = fields.Char(
        string="Condition",
        default=False,
        required=True,
    )

    description = fields.Char(
        string="Description",
        default=False,
        required=True,
    )

    minimum_months = fields.Integer(
        string="Minimum Months",
        default=False,
        required=True,
    )

    amount_type = fields.Selection(
        string="Amount Type",
        selection=[
            ("percentage", "Percentage"), 
            ("fixed_amount", "Fixed Amount")
        ],
        default="percentage",
    )

    bonus_amount = fields.Float(
        string="Amount",
        default=False,
    )

    active = fields.Boolean(
        string="Active",
        default=True,
    )

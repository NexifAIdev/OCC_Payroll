# -*- coding: utf-8 -*-
# Native Python modules

# Local python modules

# Custom python modules

# Odoo modules
from odoo import models, fields, api, _
from odoo.tools.translate import _
from odoo.exceptions import UserError, ValidationError


class SSSContribution(models.Model):
    _name = "sss.contribution"
    _snakecased_name = "sss_contribution"
    _model_path_name = "occ_payroll.model_sss_contribution"
    _description = "SSS Contribution"

    name = fields.Char(
        string="Type",
        default=False,
        required=True,
    )

    date = fields.Date(
        string="Date",
        default=False,
        required=True,
    )

    ee_regular_amount = fields.Float(
        string="EE (Regular SS)",
        default=False,
    )

    er_regular_amount = fields.Float(
        string="ER (Regular SS)",
        default=False,
    )

    ee_ec_amount = fields.Float(
        string="EE (EC)",
        default=False,
    )

    er_ec_amount = fields.Float(
        string="ER (EC)",
        default=False,
    )

    ee_mpf_amount = fields.Float(
        string="EE (MPF)",
        default=False,
    )

    er_mpf_amount = fields.Float(
        string="ER (MPF)",
        default=False,
    )

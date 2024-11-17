# -*- coding: utf-8 -*-
# Native Python modules

# Local python modules

# Custom python modules

# Odoo modules
from odoo import models, fields, api, _
from odoo.tools.translate import _
from odoo.exceptions import UserError, ValidationError


class PHICContribution(models.Model):
    _name = "phic.contribution"
    _snakecased_name = "phic_contribution"
    _model_path_name = "occ_payroll.model_phic_contribution"
    _description = "PHIC Contribution"
    
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

    ee_amount = fields.Float(
        string="EE",
        default=False,
    )

    er_amount = fields.Float(
        string="ER",
        default=False,
    )

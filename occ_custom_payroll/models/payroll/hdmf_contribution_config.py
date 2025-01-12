# -*- coding: utf-8 -*-
# Native Python modules
from datetime import datetime, date, timedelta

# Local python modules

# Custom python modules

# Odoo modules
from odoo import models, fields, api, _
from odoo.tools.translate import _
from odoo.tools import float_round
from odoo.exceptions import UserError, ValidationError
import odoo.addons.decimal_precision as dp


class HDMFContributionConfig(models.Model):
    _name = "hdmf.contribution.config"
    _description = "HDMF Contribution Table"
    _order = "id asc"

    # Range of Compensation
    range_from = fields.Float(string="Range from", help="Range (From) of Base Salary.")
    range_to = fields.Float(string="Range to", help="Range (To) of Base Salary.")

    max_compensation = fields.Float(
        string="Max Compensation", help="Maximum Compensation."
    )
    # Share
    personal_contri = fields.Float(
        string="Personal Share (Decimal Percent)",
        help="Percentage of Monthly Share - Employee Share in decimal percentage",
    )
    employer_contri = fields.Float(
        string="Employer Share (Decimal Percent)",
        help="Percentage of Monthly Share - Employer Share in decimal percentage",
    )

    def init(self):
        val = self.env["hdmf.contribution.config"].search_count([])

        if val == 0:

            vals = [
                {
                    "range_from": 0,
                    "range_to": 1500,
                    "personal_contri": 0.01,
                    "employer_contri": 0.02,
                },
                {
                    "range_from": 1501,
                    "range_to": 9999999,
                    "personal_contri": 0.02,
                    "employer_contri": 0.02,
                    "max_compensation": 5000,
                },
            ]

            for x in vals:
                self.env["hdmf.contribution.config"].create(x)


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

class PHICContributionConfig(models.Model):
    _name = "phic.contribution.config"
    _description = "PHIC Contribution Table"
    _order = "id asc"

    # Range of Compensation
    range_from = fields.Float(string="Range from", help="Range (From) of Base Salary.")
    range_to = fields.Float(string="Range to", help="Range (To) of Base Salary.")

    # Share
    personal_contri = fields.Float(string="Personal Share")
    employer_contri = fields.Float(string="Employer Share")
    monthly_premium = fields.Float(string="Monthly Premium")

    computed = fields.Boolean(
        string="Computed",
        default=False,
        help="Check if the monthly premium and individual shares are not fix amount. The system will compute using ratio with the 1st line item as the base.",
    )
    percent_decimal = fields.Float("Percent (%)")

    def init(self):
        val = self.env["phic.contribution.config"].search_count([])
        if val == 0:
            vals = [
                {
                    "range_from": 0,
                    "range_to": 10000,
                    "monthly_premium": 350,
                    "personal_contri": 175,
                    "employer_contri": 175,
                    "percent_decimal": 0,
                },
                {
                    "range_from": 10000.01,
                    "range_to": 69999.99,
                    "monthly_premium": 0,
                    "personal_contri": 0,
                    "employer_contri": 0,
                    "percent_decimal": 3.50,
                },
                {
                    "range_from": 70000,
                    "range_to": 9999999,
                    "monthly_premium": 2450,
                    "personal_contri": 1225,
                    "employer_contri": 1225,
                },
            ]
            for x in vals:
                self.env["phic.contribution.config"].create(x)

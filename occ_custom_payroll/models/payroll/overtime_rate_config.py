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

class OvertimeRateConfig(models.Model):
    _name = "overtime.rate.config"
    _description = "Rate Table Configuration"
    _order = "id asc"

    name = fields.Char()
    rate_id = fields.Integer()
    percentage = fields.Float(
        default=1, digits=(2, 3), help="Percentage of pay in decimal."
    )

    def init(self):
        val = self.env["overtime.rate.config"].search_count([])

        if val == 0:

            vals = [
                {"rate_id": 0, "name": "Ordinary Day", "percentage": 1},
                {
                    "rate_id": 1,
                    "name": "Rest Day",
                    "percentage": 1.3,
                },  # Sunday or Rest day
                {"rate_id": 2, "name": "Special Day", "percentage": 1.3},
                {
                    "rate_id": 3,
                    "name": "Special day falling on rest day",
                    "percentage": 1.5,
                },
                {"rate_id": 4, "name": "Regular Holiday", "percentage": 2},
                {
                    "rate_id": 5,
                    "name": "Regular Holiday falling on rest day",
                    "percentage": 2.6,
                },
                {"rate_id": 6, "name": "Double Holiday", "percentage": 3},
                {
                    "rate_id": 7,
                    "name": "Double Holiday falling on rest day",
                    "percentage": 3.9,
                },
                {"rate_id": 8, "name": "Ordinary Day, night shift", "percentage": 1.1},
                {"rate_id": 9, "name": "Rest Day, night shift", "percentage": 1.43},
                {"rate_id": 10, "name": "Special Day, night shift", "percentage": 1.43},
                {
                    "rate_id": 11,
                    "name": "Special Day, rest day, night shift",
                    "percentage": 1.65,
                },
                {
                    "rate_id": 12,
                    "name": "Regular Holiday, night shift",
                    "percentage": 2.2,
                },
                {
                    "rate_id": 13,
                    "name": "Regular Holiday, rest day, night shift",
                    "percentage": 2.86,
                },
                {
                    "rate_id": 14,
                    "name": "Double Holiday, night shift",
                    "percentage": 3.3,
                },
                {
                    "rate_id": 15,
                    "name": "Double Holiday, rest day, night shift",
                    "percentage": 4.29,
                },
                {"rate_id": 16, "name": "Ordinary day, overtime", "percentage": 1.25},
                {"rate_id": 17, "name": "Rest day, overtime", "percentage": 1.69},
                {"rate_id": 18, "name": "Special day, overtime", "percentage": 1.69},
                {
                    "rate_id": 19,
                    "name": "Special day, rest day, overtime",
                    "percentage": 1.95,
                },
                {
                    "rate_id": 20,
                    "name": "Regular Holiday, overtime",
                    "percentage": 2.60,
                },
                {
                    "rate_id": 21,
                    "name": "Regular Holiday, rest day, overtime",
                    "percentage": 3.38,
                },
                {"rate_id": 22, "name": "Double Holiday, overtime", "percentage": 3.9},
                {
                    "rate_id": 23,
                    "name": "Double Holiday, rest day, overtime",
                    "percentage": 5.07,
                },
                {
                    "rate_id": 24,
                    "name": "Ordinary Day, night shift, OT",
                    "percentage": 1.375,
                },
                {
                    "rate_id": 25,
                    "name": "Rest Day, night shift, OT",
                    "percentage": 1.859,
                },
                {
                    "rate_id": 26,
                    "name": "Special Day, night shift, OT",
                    "percentage": 1.859,
                },
                {
                    "rate_id": 27,
                    "name": "Special Day, rest day, night shift, OT",
                    "percentage": 2.145,
                },
                {
                    "rate_id": 28,
                    "name": "Regular Holiday, night shift, OT",
                    "percentage": 2.86,
                },
                {
                    "rate_id": 29,
                    "name": "Regular Holiday, rest day, night shift, OT",
                    "percentage": 3.718,
                },
                {
                    "rate_id": 30,
                    "name": "Double Holiday, night shift, OT",
                    "percentage": 4.29,
                },
                {
                    "rate_id": 31,
                    "name": "Double Holiday, rest day, night shift, OT",
                    "percentage": 5.577,
                },
            ]

            for x in vals:
                self.env["overtime.rate.config"].create(x)
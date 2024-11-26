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

class LateUndertimeConfig(models.Model):
    _name = "late.undertime.config"
    _description = "Late/Undertime Percentage Configuration"
    _order = "id asc"

    config_type = fields.Selection(
        [("late", "Late"), ("undertime", "Undertime")], string="Type", default="late"
    )
    min_from = fields.Float(default=1, help="Number of minutes late: From")
    min_to = fields.Float(default=1, help="Number of minutes late: To")

    percentage = fields.Float(default=0.25, help="Percentage of deduction in decimal.")

    def init(self):
        val = self.env["late.undertime.config"].search_count([])

        if val == 0:

            vals = [
                {
                    "config_type": "late",
                    "min_from": 1,
                    "min_to": 15,
                    "percentage": 0.15,
                },
                {
                    "config_type": "late",
                    "min_from": 16,
                    "min_to": 30,
                    "percentage": 0.5,
                },
                {
                    "config_type": "late",
                    "min_from": 31,
                    "min_to": 45,
                    "percentage": 0.75,
                },
                {"config_type": "late", "min_from": 46, "min_to": 60, "percentage": 1},
            ]

            for x in vals:
                self.env["late.undertime.config"].create(x)
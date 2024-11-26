# -*- coding: utf-8 -*-
# Native Python modules
import calendar
from calendar import monthrange

# Local python modules

# Custom python modules

# Odoo modules
from odoo import models, fields, api, _
from odoo.tools.translate import _
from odoo.exceptions import UserError, ValidationError

class PaycutMixin(models.AbstractModel):
    _name = "paycut.mixin"
    _description = "Paycut Mixin"
    
    def get_last_day_of_month(self, year, month):
        if month < 1 or month > 12:
            raise ValueError("Month must be between 1 and 12.")
        if year < 1:
            raise ValueError("Year must be a positive integer.")
        
        last_day = monthrange(year, month)[1]
        
        return {
            "first_day": 1,
            "middle_day": 15,
            "last_day": last_day,
        }

    @api.model
    def _get_paycut_period(self, year, month):
        
        periods = self.get_last_day_of_month(year, month)
        
        paycut_first_half = self.env["paycut.configuration"].search(
            domain=[
                ("start_day", "=", periods["first_day"]),
                ("end_day", "=", periods["middle_day"]),
            ],
            limit=1
        )
        
        paycut_second_half = self.env["paycut.configuration"].search(
            domain=[
                ("start_day", "=", periods["middle_day"] + 1),
                ("end_day", "=", periods["last_day"]),
            ],
            limit=1
        )
        
        return {
            "first_half": paycut_first_half.id if paycut_first_half else False,
            "second_half": paycut_second_half.id if paycut_second_half else False,
        }
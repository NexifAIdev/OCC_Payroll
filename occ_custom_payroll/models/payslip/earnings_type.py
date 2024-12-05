# -*- coding: utf-8 -*-
# Native Python modules

# Local python modules

# Custom python modules

# Odoo modules
from odoo import models, fields, api, _
from odoo.tools.translate import _
from odoo.exceptions import UserError, ValidationError

class earnings_type(models.Model):
    _name = "earnings.type"

    name = fields.Char("Name of Earning")
    active = fields.Boolean(default=True)
    sequence = fields.Integer()

    def init(self):
        val = self.env["earnings.type"].search_count([])

        if val == 0:

            vals = [
                {"sequence": 1, "name": "Base Salary", "active": True},
                {"sequence": 2, "name": "Overtime", "active": True},
                {"sequence": 3, "name": "Night Differential", "active": True},
                {"sequence": 4, "name": "Holiday Pay", "active": True},
                {"sequence": 5, "name": "Leave Pay", "active": True},
                {"sequence": 6, "name": "Adjustment: Salary", "active": True},
            ]

            for x in vals:
                self.env["earnings.type"].create(x)
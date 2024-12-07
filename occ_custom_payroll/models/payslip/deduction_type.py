# -*- coding: utf-8 -*-
# Native Python modules

# Local python modules

# Custom python modules

# Odoo modules
from odoo import models, fields, api, _
from odoo.tools.translate import _
from odoo.exceptions import UserError, ValidationError

class deduction_type(models.Model):
    _name = "deduction.type"

    name = fields.Char("Name of Deduction")
    active = fields.Boolean(default=True)
    sequence = fields.Integer()

    def init(self):
        val = self.env["deduction.type"].search_count([])

        if val == 0:

            vals = [
                {"sequence": 1, "name": "SSS Contribution", "active": True},
                {"sequence": 2, "name": "PHIC Contribution", "active": True},
                {"sequence": 3, "name": "HDMF Contribution", "active": True},
                {"sequence": 4, "name": "Tardiness", "active": True},
                {"sequence": 5, "name": "Undertime", "active": True},
                {"sequence": 6, "name": "Leave w/o pay", "active": True},
                {"sequence": 7, "name": "Adjustment: Salary", "active": True},
            ]

            for x in vals:
                self.env["deduction.type"].create(x)
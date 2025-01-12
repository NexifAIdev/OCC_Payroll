# -*- coding: utf-8 -*-
# Native Python modules

# Local python modules

# Custom python modules

# Odoo modules
from odoo import models, fields, api, _
from odoo.tools.translate import _
from odoo.exceptions import UserError, ValidationError


class nontaxable_type(models.Model):
    _name = "nontaxable.type"

    name = fields.Char("Non Taxable Item")
    active = fields.Boolean(default=True)
    sequence = fields.Integer()

    def init(self):
        val = self.env["nontaxable.type"].search_count([])

        if val == 0:

            vals = [
                {"sequence": 1, "name": "Reimbursement", "active": True},
                {"sequence": 2, "name": "Allowance", "active": True},
                {"sequence": 3, "name": "Other Charges", "active": True},
                {"sequence": 4, "name": "Commission", "active": True},
                {"sequence": 5, "name": "Loan Deductions", "active": True},
            ]

            for x in vals:
                self.env["nontaxable.type"].create(x)

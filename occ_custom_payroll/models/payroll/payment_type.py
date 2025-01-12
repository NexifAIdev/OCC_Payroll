# -*- coding: utf-8 -*-
# Native Python modules

# Local python modules

# Custom python modules

# Odoo modules
from odoo import models, fields, api, _
from odoo.tools.translate import _
from odoo.exceptions import UserError, ValidationError


class PaymentType(models.Model):
    _name = "payment.type"
    _description = "Salary Payment Type"
    _order = "sequence, id"

    name = fields.Char(string="Payment Type", required=True)
    account_id = fields.Many2one("account.account", string="Account")
    company_id = fields.Many2one("res.company", string="Company")
    sequence = fields.Integer(
        help="Gives the sequence when displaying a list of Payment Type.", default=10
    )

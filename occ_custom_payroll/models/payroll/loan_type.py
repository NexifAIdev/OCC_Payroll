# -*- coding: utf-8 -*-
# Native Python modules

# Local python modules

# Custom python modules

# Odoo modules
from odoo import models, fields, api, _
from odoo.tools.translate import _
from odoo.exceptions import UserError, ValidationError


class LoanType(models.Model):
    _name = "loan.type"

    name = fields.Char(string="Loan")
    gl_account = fields.Many2one("account.account", string="GL Account")
    company_id = fields.Many2one("res.company")

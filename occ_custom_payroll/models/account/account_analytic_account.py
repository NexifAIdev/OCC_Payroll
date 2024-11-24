# -*- coding: utf-8 -*-
# Native Python modules

# Local python modules

# Custom python modules

# Odoo modules
from odoo import models, fields, api, _
from odoo.tools.translate import _
from odoo.exceptions import UserError, ValidationError

class account_analytic_account(models.Model):
    _inherit = "account.analytic.account"

    analytic_tag_ids = fields.Many2many("account.analytic.tag", string="Analytic Tag")

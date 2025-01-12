# -*- coding: utf-8 -*-
# Native Python modules

# Local python modules

# Custom python modules

# Odoo modules
from odoo import models, fields, api, _
from odoo.tools.translate import _
from odoo.exceptions import UserError, ValidationError


class UnpaidLeaves(models.Model):
    _inherit = "hr.leave.type"

    is_unpaid_leave = fields.Boolean(string="Unpaid Leave", default=False, copy=False)
    company_id = fields.Many2one("res.company", string="Company")

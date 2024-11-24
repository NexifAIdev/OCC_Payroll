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

class OvertimeRequestLine(models.Model):
    _name = "overtime.breakdown.line"

    ot_line_id = fields.Many2one("overtime.request.line")
    date = fields.Date()
    rate_type = fields.Selection(
        ratetype_list, string="Type", store=True, compute="get_rate_type"
    )
    rate = fields.Float(store=True, compute="get_rate_type")
    hours = fields.Float(store=True, compute="get_rate_type")
    hourly_rate = fields.Float()
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


class payslip_leave_line(models.Model):
    _name = "payslip.leave.line"

    payslip_id = fields.Many2one(
        "exhr.payslip", string="Payslip", store=True, index=True
    )
    leaves_id = fields.Many2one("hr.leave", "Time off")
    holiday_status_id = fields.Many2one("hr.leave.type", "Time Off Type")
    days = fields.Float("Days covered in payslip")

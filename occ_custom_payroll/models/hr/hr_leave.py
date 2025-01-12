# -*- coding: utf-8 -*-
# Native Python modules

# Local python modules

# Custom python modules

# Odoo modules
from odoo import models, fields, api, _
from odoo.tools.translate import _
from odoo.exceptions import UserError, ValidationError


class CustomHalfHolidaysRequest(models.Model):
    _inherit = "hr.leave"

    payslip_status = fields.Boolean(track_visibility="onchange")

    @api.onchange("request_date_from_period", "request_unit_half")
    def _onchange_durations(self):
        if self.request_unit_half:
            if self.request_date_from_period:
                self.number_of_days = 0.5

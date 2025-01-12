# -*- coding: utf-8 -*-
# Native Python modules
from datetime import datetime, date, time, timedelta

# Local python modules

# Custom python modules

# Odoo modules
from odoo import models, fields, api, _
from odoo.tools.translate import _
from odoo.exceptions import UserError, ValidationError


class DialogAttendanceSheet(models.TransientModel):
    _name = "dialog.attendance.sheet"

    def request_update_attendance_sheet(self):
        context = dict(self._context or {})
        active_ids = context.get("active_ids", []) or []
        request_ids = tuple(active_ids)

        for x in (
            self.env["hr.attendance.sheet"].sudo().search([("id", "in", request_ids)])
        ):
            x.update_attendance_sheet()

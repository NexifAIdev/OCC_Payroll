# -*- coding: utf-8 -*-
# Native Python modules
from datetime import datetime, date, time, timedelta

# Local python modules

# Custom python modules
import pytz
from pytz import timezone

# Odoo modules
from odoo import models, fields, api, _
from odoo.tools.translate import _
from odoo.exceptions import UserError, ValidationError


class HRImportAttendanceLine(models.Model):
    _name = "hr.import.attendance.line"

    employee_id = fields.Many2one("hr.employee", string="Employee Name (Odoo)")
    name = fields.Char(string="Employee Name (Excel)", required=True)
    date_from = fields.Char(string="Date (From)")
    hour_from = fields.Char(string="Hour (From)")
    date_to = fields.Char(string="Date (To)")
    hour_to = fields.Char(string="Hour (To)")

    datestamp_from = fields.Char(string="Datestamp (From)")
    datestamp_to = fields.Char(string="Datestamp (To)")

    employee_attendance_id = fields.Many2one(
        "import.employee.attendance", string="Employee Attendance", copy=False
    )

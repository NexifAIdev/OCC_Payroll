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


class HRImportAttendance(models.Model):
    _name = "hr.import.attendance"
    _inherit = ["occ.payroll.cfg", "mail.thread"]
    _description = "Employee Attendance Sheet"
    _order = "create_date desc"

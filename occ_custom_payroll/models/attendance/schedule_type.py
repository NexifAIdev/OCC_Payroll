# -*- coding: utf-8 -*-
# Native Python modules
from datetime import datetime, date, time, timedelta

# Local python modules

# Custom python modules

# Odoo modules
from odoo import models, fields, api, _
from odoo.tools.translate import _
from odoo.exceptions import UserError, ValidationError


class ScheduleType(models.Model):
    _name = "schedule.type"

    name = fields.Char()
    external_id = fields.Integer("External ID")
    color = fields.Integer("Color Index", default=10)
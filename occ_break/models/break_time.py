# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import pytz

from collections import defaultdict
from datetime import datetime, timedelta
from operator import itemgetter
from pytz import timezone

from odoo.http import request
from odoo import models, fields, api, exceptions, _
from odoo.addons.resource.models.utils import Intervals
from odoo.osv.expression import AND, OR
from odoo.tools.float_utils import float_is_zero
from odoo.exceptions import AccessError, UserError
from odoo.tools import format_duration, format_time, format_datetime

class HrAttendance(models.Model):
	_inherit = "hr.attendance"
	
	break_ids = fields.One2many('break.time','attendance_id', string="Breaks")

class BreakTime(models.Model):
	_name = "break.time"
	
	name = fields.Char()
	attendance_id = fields.Many2one('hr.attendance', string="Attendance Record")
	break_start = fields.Datetime(string="Start Break", tracking=True)
	break_end = fields.Datetime(string="End Break", tracking=True)

	total_break_duration = fields.Float(string='Total Break Duration (minutes)', compute="_compute_break_difference", readonly=True)


	@api.depends('break_start', 'break_end')
	def _compute_break_difference(self):
		for rec in self:
			if rec.break_start and rec.break_end:
				time_difference = rec.break_end - rec.break_start
				rec.total_break_duration = time_difference.total_seconds() / 60.0
			else:
				rec.total_break_duration = 0.0


	
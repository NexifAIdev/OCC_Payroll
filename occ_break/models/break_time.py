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

	@api.depends('check_in', 'check_out','break_ids')
	def _compute_worked_hours(self):
		for attendance in self:
			if attendance.check_out and attendance.check_in and attendance.employee_id:
				calendar = attendance._get_employee_calendar()
				resource = attendance.employee_id.resource_id
				tz = timezone(calendar.tz)
				check_in_tz = attendance.check_in.astimezone(tz)
				check_out_tz = attendance.check_out.astimezone(tz)
				lunch_intervals = attendance.employee_id._employee_attendance_intervals(check_in_tz, check_out_tz, lunch=True)
				attendance_intervals = Intervals([(check_in_tz, check_out_tz, attendance)]) - lunch_intervals
				delta = sum((i[1] - i[0]).total_seconds() for i in attendance_intervals)
				attendance.worked_hours = delta / 3600.0
			else:
				attendance.worked_hours = False

			# 
			if attendance.check_out and attendance.check_in and attendance.employee_id:
				break_hour_summary = 0
				if attendance.break_ids:
					for br in attendance.break_ids:
						break_hour_summary += br.total_break_duration
				
				# GET BREAK DIFFERENCE FROM EMPLOYEE AND ATTENDANCE
				break_difference = break_hour_summary - attendance.employee_id.total_break_hours 

				attendance.worked_hours = attendance.worked_hours - break_difference

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
				rec.total_break_duration = time_difference.total_seconds() / 3600
			else:
				rec.total_break_duration = 0.0


	
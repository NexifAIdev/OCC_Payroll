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


class HrEmployee(models.Model):
	_inherit = "hr.employee"
	
	# BREAK
	
	# end_lunch = fields.Float(string="End Lunch", tracking=True,default=0.0)

	# ADD START LUNCH TO DISPLAY THE START OF LUNCH
	start_lunch = fields.Float(string="Start Lunch", tracking=True,default=0.0)

	# ADD "IS BREAK" TO DETERMINE IF EMPLOYEE IS ON BREAK
	is_break = fields.Boolean()

	# ADD "IS BREAK DONE" TO CHECK
	is_break_done = fields.Boolean(compute="_check_employee_break")


	# TOTAL DURATION OF BREAK HOURS
	total_break_hours = fields.Float(default=1.0)
	is_field_visible_on_manager = fields.Boolean(compute="_is_field_visible_on_manager")

	@api.depends('parent_id','approver2_id')
	def _is_field_visible_on_manager(self):
		for rec in self:
			if self.env.user.id == rec.parent_id.user_id.id or self.env.user.id == rec.approver2_id.user_id.id:
				rec.is_field_visible_on_manager = True
			else:
				rec.is_field_visible_on_manager = False


	@api.depends('attendance_ids.start_lunch', 'attendance_ids.end_lunch')
	def _check_employee_break(self):
		for rec in self:
			attendance = self.env['hr.attendance'].search([('employee_id', '=', rec.id)], order="id desc", limit=1)

			# print("\n\n\n\nChecking Attendance Here!")
			# print(attendance)
			# print(attendance.end_lunch)
			# print(attendance.check_out)
			if attendance.end_lunch and not attendance.check_out:
				rec.is_break_done = True
			else:
				rec.is_break_done = False


	# IF EMPLOYEE CHECK OUT WITHOUT ENDING LUNCH
	def _attendance_action_change(self, geo_information=None):

		res = super(HrEmployee, self)._attendance_action_change(geo_information=geo_information)
		attendance = self.env['hr.attendance'].search([('employee_id', '=', self.id)], order="id desc", limit=1)
		break_date = fields.Datetime.now()

		print("get attendance ction change")
		print(attendance)
		print(attendance.start_lunch)
		print(attendance.end_lunch)

		if attendance.check_in and attendance.check_out and attendance.is_break:
			
			print("break time exist")
			existing_break = self.env['break.time'].search([('attendance_id', '=', attendance.id), ('break_end', '=', False)], limit=1)
			print(existing_break)
			existing_break.write({
				'break_end': break_date,
			})

			# UPDATE ATTENDANCE BREAK STATUS
			attendance.is_break = False

			# UPDATE ON EMPLOYEE RECORD
			self.is_break = False
			self.start_lunch = 0
			

		return res

	def _break_action_change(self):
		""" Check In/Check Out action
			Check In: create a new attendance record
			Check Out: modify check_out field of appropriate attendance record
		"""
		self.ensure_one()
		break_date = fields.Datetime.now()
		attendance = self.env['hr.attendance'].search([('employee_id', '=', self.id), ('check_out', '=', False)], limit=1)
		
		if attendance and not attendance.is_break :
			break_values = {
				'attendance_id': attendance.id,
				'break_start': break_date,
				
			}

			# UPDATE ATTENDANCE BREAK STATUS
			attendance.is_break = True

			self.env['break.time'].create(break_values)

			# Add 8 Hours
			start_lunch = break_date + timedelta(hours=8)
			# Extract the time
			time_value = start_lunch.time()
			# Convert time to float hours (hours + minutes/60 + seconds/3600)
			start_hours = time_value.hour + time_value.minute / 60 + time_value.second / 3600
			print("Starting Hours for Employee: ",start_hours)
			# FOR DISPLAY
			self.start_lunch = start_hours


			

			

		else:

			existing_break = self.env['break.time'].search([('attendance_id', '=', attendance.id), ('break_end', '=', False)], limit=1)

			
			# duration = (break_date - existing_break.break_start).total_seconds() / 60.0
			existing_break.write({
				'break_end': break_date,
				# 'total_break_duration': duration
			})

			# UPDATE ATTENDANCE BREAK STATUS
			attendance.is_break = False



		return attendance
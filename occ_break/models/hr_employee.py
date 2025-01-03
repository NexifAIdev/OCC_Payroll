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
	start_lunch = fields.Float(string="Start Lunch", tracking=True,default=0.0)
	end_lunch = fields.Float(string="End Lunch", tracking=True,default=0.0)
	is_break = fields.Boolean()


	def _break_action_change(self):
		""" Check In/Check Out action
			Check In: create a new attendance record
			Check Out: modify check_out field of appropriate attendance record
		"""
		self.ensure_one()
		break_date = fields.Datetime.now()
		attendance = self.env['hr.attendance'].search([('employee_id', '=', self.id), ('check_out', '=', False)], limit=1)
		# employee = self.env['hr.employee'].search([('id', '=', self.id)], limit=1)
		
		if attendance and not attendance.is_break :
			attendance.write({
				'start_lunch': break_date,
				'is_break': True,
			})

			# Add 8 Hours
			start_lunch = attendance.start_lunch + timedelta(hours=8)
			# Extract the time
			time_value = start_lunch.time()
			# Convert time to float hours (hours + minutes/60 + seconds/3600)
			start_hours = time_value.hour + time_value.minute / 60 + time_value.second / 3600
			print("Starting Hours for Employee: ",start_hours)
			self.start_lunch = start_hours


			

		else:
			attendance.write({
				'end_lunch': break_date,
				'is_break': False,
			})

		# if self.attendance_state != 'checked_in':
		#     if geo_information:
		#         vals = {
		#             'employee_id': self.id,
		#             'check_in': action_date,
		#             **{'in_%s' % key: geo_information[key] for key in geo_information}
		#         }
		#     else:
		#         vals = {
		#             'employee_id': self.id,
		#             'check_in': action_date,
		#         }
		#     return self.env['hr.attendance'].create(vals)
		# attendance = self.env['hr.attendance'].search([('employee_id', '=', self.id), ('check_out', '=', False)], limit=1)
		# if attendance:
		#     if geo_information:
		#         attendance.write({
		#             'check_out': action_date,
		#             **{'out_%s' % key: geo_information[key] for key in geo_information}
		#         })
		#     else:
		#         attendance.write({
		#             'check_out': action_date
		#         })
		# else:
		#     raise exceptions.UserError(_(
		#         'Cannot perform check out on %(empl_name)s, could not find corresponding check in. '
		#         'Your attendances have probably been modified manually by human resources.',
		#         empl_name=self.sudo().name))
		return attendance
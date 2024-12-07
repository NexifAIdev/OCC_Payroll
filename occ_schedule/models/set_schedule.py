import base64
from odoo import models, api, fields, _
from odoo.exceptions import AccessError, UserError  
from datetime import date, timedelta, datetime

class EmployeeSetSchedule(models.TransientModel):
	_name = 'set.schedule'
	_description = 'Set Schedule'

	employee_ids = fields.Many2many('hr.employee')
	week_number = fields.Integer()

	def create_schedules(self):
		print("gg")
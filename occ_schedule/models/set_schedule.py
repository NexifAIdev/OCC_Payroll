import base64
from odoo import models, api, fields, _
from odoo.exceptions import AccessError, UserError  
from datetime import date, timedelta, datetime
import pytz

# class EmployeeSetSchedule(models.TransientModel):
# 	_name = 'set.schedule'
# 	_description = 'Set Schedule'

# 	employee_ids = fields.Many2many('hr.employee')
# 	week_number = fields.Integer()

# 	def create_schedules(self):
# 		print("gg")


class EmployeeSetSchedule(models.TransientModel):
	_name = 'set.schedule'
	_description = 'Set Schedule'

	
	employee_ids = fields.Many2many('hr.employee', string="Employees")

	current_week = fields.Integer()
	week_number = fields.Selection(
		selection=[(str(i), 'Week ' + str(i)) for i in range(1, 53)],
		string="Select Week",
		required=True
	)

	def _get_year_selection(self):
		current_year = datetime.now().year
		year_range = range(current_year - 10, current_year + 11)
		return [(str(year), str(year)) for year in year_range]

	year = fields.Selection(_get_year_selection, string='Year')

	current_year = fields.Char()
	# year = fields.Char()


	def get_week_dates(self, week, year):

		first_day_of_year = datetime(year, 1, 1)
		delta = timedelta(days=week * 7 - 1)
		start_date = first_day_of_year + delta

		# Adjust the start date to the nearest Monday
		while start_date.weekday() != 0:
			start_date -= timedelta(days=1)

		end_date = start_date + timedelta(days=4)

		week_dates = []
		for date in range(5):
			day = start_date + timedelta(days=date)
			week_dates.append(day.strftime("%m-%d-%Y"))

		return week_dates


	def create_schedules(self): 
		for rec in self:
			
			if not rec.week_number:
				raise UserError("No week number indicated!")
			if not rec.year:
				raise UserError("No year indicated!")

			if rec.employee_ids:

				print("Employee: ",rec.employee_ids)

				week = int(rec.week_number)
				year = int(rec.year)

				print("Week Dates: ",rec.get_week_dates(week,year))
				week_dates = rec.get_week_dates(week,year)
				
				for emp in rec.employee_ids:

					for days in week_dates:
						
						day_count = datetime.strptime(days, '%m-%d-%Y').weekday()

						hour_from = self.env['resource.calendar.attendance'].search([
									('calendar_id', '=', emp.resource_calendar_id.id),
									('dayofweek', '=', day_count),
									('day_period', '=', 'morning'),
								], limit=1, order='dayofweek asc').hour_from

						hour_to = self.env['resource.calendar.attendance'].search([
									('calendar_id', '=', emp.resource_calendar_id.id),
									('dayofweek', '=', day_count),
									('day_period', '=', 'afternoon'),
								], limit=1, order='dayofweek asc').hour_to


						date = datetime.strptime(days, '%m-%d-%Y')
						# NOT SURE WHY I NEED TO SET -8
						start = date + timedelta(hours=hour_from-8)
						end = date + timedelta(hours=hour_to-8)


						print(start)
						print(end)
							
						start_datetime = datetime.strptime(str(start), '%Y-%m-%d %H:%M:%S')
						end_datetime = datetime.strptime(str(end), '%Y-%m-%d %H:%M:%S')


						# Original datetime in local time (naive)
						local_sd = start_datetime
						local_ed = end_datetime

						# Convert to UTC
						utc_sd = local_sd.replace(tzinfo=None)
						utc_ed = local_ed.replace(tzinfo=None)

						# print("UTC Datetime:", utc_dt)
						# Convert to the desired format
						# start_datetime = start_datetime.strftime('%d-%m-%Y %H:%M:%S')
						# end_datetime = end_datetime.strftime('%d-%m-%Y %H:%M:%S')

						print(start_datetime)
						print(end_datetime)

						schedule_date = {
							'name': emp.name,
							'week_number': week,
							'employee_id': emp.id,
							'start_datetime': utc_sd,
							'end_datetime': utc_ed,
							'resource_calendar_id': emp.resource_calendar_id.id,
						}

						print(schedule_date)

						self.env['schedule.management'].create(schedule_date)
			else:
				raise UserError("No Employee Selected!")
					
				


				

			


	# def create_schedules(self):
	#     """This method is called when the user confirms the selected week."""
	#     if not self.employee_ids:
	#         raise UserError(_("Please select at least one employee."))

		
	#     for employee in self.employee_ids:
	#         employee.write({'schedule_week': self.week_number})   
	#     return {'type': 'ir.actions.act_window_close'}

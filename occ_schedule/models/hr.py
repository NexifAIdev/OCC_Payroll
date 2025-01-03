import base64
from odoo import models, api, fields, _
from odoo.exceptions import AccessError, UserError  
from datetime import date, timedelta, datetime


class HREmployee(models.Model):
	_inherit = "hr.employee"

	# 0 = MONDAY    
	# 1 = TUESDAY
	# 2 = WEDNESDAY
	# 3 = THURSDAY
	# 4 = FRIDAY
	# 5 = SATURDAY
	# 6 = SUNDAY

	# morning = Morning
	# afternoon = Afternoon
	
	def action_assign_weekly_schedule(self):

		current_week = datetime.now().isocalendar()[1]
		week_number = str(current_week)
		current_year = datetime.now().year

		return {
			'type': 'ir.actions.act_window',
			'name': 'Assign Weekly Schedule',
			'res_model': 'set.schedule',
			'view_mode': 'form',
			'view_id': self.env.ref('occ_schedule.view_set_schedule_form').id,
			'target': 'new',
			'context': {
					'default_employee_ids': self.ids,
					'default_current_week': current_week,
					'default_week_number': week_number,
					'default_current_year': str(current_year),
					'default_year': str(current_year),
					},
		}

	# @api.onchange('resource_calendar_id')
	# def _onchange_resource_calendar(self):
	# 	for rec in self:
	# 		current_week = datetime.now().isocalendar()[1]
	# 		sched_week = self.env['schedule.management'].search([('week_number','=',current_week),('employee_id','=',rec.id)])
	# 		# CHECK IF EMPLOYEE RECORD IS ALREADY CREATED
	# 		if not sched_week:

	# 			calendar_attendance = self.env['resource.calendar.attendance'].search([
	# 						('calendar_id', '=', rec.resource_calendar_id.id),
	# 						('dayofweek', '=', reference_day),
	# 						('day_period', '=', 'morning'),
	# 					], order='dayofweek asc')
				
	# 			for att in calendar_attendance:

	# 				hour_from = self.env['resource.calendar.attendance'].search([
	# 							('calendar_id', '=', rec.resource_calendar_id.id),
	# 							('dayofweek', '=', att.dayofweek),
	# 							('day_period', '=', 'morning'),
	# 						], limit=1, order='dayofweek asc')
	# 				hour_to = self.env['resource.calendar.attendance'].search([
	# 							('calendar_id', '=', rec.resource_calendar_id.id),
	# 							('dayofweek', '=', att.dayofweek),
	# 							('day_period', '=', 'afternoon'),
	# 						], limit=1, order='dayofweek asc')

				

	# 				schedule_date = {
	# 					'week_number': current_week,
	# 					'employee_id': rec.id,
	# 					'start_datetime': hour_from,
	# 					'end_datetime': hour_to,
						
	# 				}

	# 				self.env['schedule.management'].create(partner_data)

	# 			hour_from = 0
	# 			hour_to = 0

	# 			for att in calendar_attendance:
	# 				if att.day_period == 'morning':
	# 					hour_from = att.hour_from
	# 				if att.day_period == 'afternoon':
	# 					hour_to = att.hour_to
				






	# 		print("week today baboy?",current_week)


	# @api.onchange('resource_calendar_id')
	# def _onchange_resource_calendar(self):
	#     for rec in self:
	#         if rec.resource_calendar_id:

	#                 today = datetime.today()                    
	#                 reference_day = today.weekday()

	#                 print("Reference Day",reference_day)
	#                 calendar_attendance = self.env['resource.calendar.attendance'].search(
	#                     [
	#                         ('calendar_id', '=', rec.resource_calendar_id.id),
	#                         ('dayofweek', '=', reference_day)

	#                     ], order='dayofweek asc')

	#                 for att in calendar_attendance:

	#                     print("Day Period",att.day_period)
	#                     if att.day_period == 'morning':
	#                         rec.hour_from = att.hour_from
	#                         print("Hour from",att.hour_from)
	#                     if att.day_period == 'afternoon':
	#                         rec.hour_to = att.hour_to
	#                         print("Hour To",att.hour_to)
	#         else:
	#             rec.hour_from = False
	#             rec.hour_to = False




	# @api.depends('resource_calendar_id')
	# def _compute_start_datetime(self):
	#     for record in self:
	#         if record.resource_calendar_id:
	#             # Set the reference date (e.g., today)
	#             reference_date = fields.Date.context_today(self)
	#             print(reference_date)
	#             # Get the first working interval for the day from the calendar
	#             # working_intervals = record.resource_calendar_id._work_intervals_batch(
	#             #     reference_date, reference_date + timedelta(days=1), resource_id=record.resource_calendar_id.id
	#             # )[record.resource_calendar_id.id]

	#             # Find the first interval start time if it exists
	#             if working_intervals:
	#                 record.start_datetime = working_intervals[0][0]  # [0][0] is the start of the first interval
	#                 record.end_datetime = working_intervals[-1][1]  # End of the last interval
	#             else:
	#                 record.start_datetime = False
	#                 record.end_datetime = False
	#         else:
	#             record.start_datetime = False
	#             record.end_datetime = False


#     @api.model
#     def update_schedule_management(self):
#         employee_ids = self.env.context.get('active_ids') 
#         if employee_ids:
#             employees = self.env['hr.employee'].browse(employee_ids)
#             updated_schedule = "New Schedule Info"  # Ano kaya lalagay ko kuys

#             for employee in employees:
#                 if hasattr(employee, 'schedule_id'):
#                     employee.schedule_id = updated_schedule  # thinking pa
#                 else:
#                     raise UserError(_("Schedule field does not exist for employee: %s" % employee.name))

#             return {
#                 'type': 'ir.actions.client',
#                 'tag': 'reload',
#                 'name': _('Schedule Update'),
#                 'message': _('The schedule for selected employees has been successfully updated.'),
#             }
#         else:
#             raise UserError(_("No active employees found for updating the schedule."))
	

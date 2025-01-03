import base64
from odoo import models, api, fields, _
from odoo.exceptions import AccessError, UserError  
from datetime import date, timedelta, datetime

class ScheduleManagement(models.Model):
	_name = 'schedule.management'
	_description = "Schedule Management"

	name = fields.Char()
	
	employee_id = fields.Many2one(
		'hr.employee', 
		string="Employee", 
		required=True,
		domain="[('parent_id', '=', manager_id)]"  # Show employees under the selected manager/ not sure what is the id
	)
	resource_calendar_id = fields.Many2one('resource.calendar', string="Assigned Schedule", required=True)

	week_number = fields.Integer()
	start_datetime = fields.Datetime('Start', tracking=True)
	end_datetime = fields.Datetime('End', tracking=True)

	manager_id = fields.Many2one(
		'hr.employee', 
		string="Manager", 
		default=lambda self: self.env.user.employee_id.id,
		readonly=True
	)

	
	def action_custom_button(self):
		# Make sure the action works even if no specific record is selected
		if not self:
			# You can perform a generic action here or return a warning if no records are selected
			return {
				'type': 'ir.actions.client',
				'tag': 'reload',
				'name': 'Custom Action',
				'params': {
					'message': 'Button clicked with no specific record.',
				}
			}
		
		# If there are records, perform your desired action
		return {
			'type': 'ir.actions.client',
			'tag': 'reload',
			'name': 'Custom Action',
			'params': {
				'message': 'Action executed on selected records.',
			}
		}

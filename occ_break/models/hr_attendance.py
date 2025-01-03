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
	
	# BREAK
	start_lunch = fields.Datetime(string="Start Lunch", tracking=True)
	end_lunch = fields.Datetime(string="End Lunch", tracking=True)

	break_hours = fields.Float(compute="_compute_time_difference")
	is_break = fields.Boolean(default=False)
	

	@api.depends('start_lunch', 'end_lunch')
	def _compute_time_difference():
		for rec in self:
			if rec.start_date and rec.end_date:
				# Calculate time difference in hours
				time_difference = rec.end_date - rec.start_date
				rec.break_hours = time_difference.total_seconds() / 3600
			else:
				rec.break_hours = False

	 


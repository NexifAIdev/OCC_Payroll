# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import http, _
from odoo.http import request
from odoo.tools import float_round
from odoo.tools.image import image_data_uri

import datetime

class HrAttendance(http.Controller):

    @staticmethod
    def _get_break_data(employee):
        response = {}
        if employee:

            now = datetime.datetime.now()
            hours = now.hour
            minutes = now.minute
            seconds = now.second
            current_time = hours + minutes / 60 + seconds / 3600
            duration = current_time - employee.start_lunch
            response = {
                'id': employee.id,
                'is_break': employee.is_break,
                'start_lunch': float_round(employee.start_lunch, precision_digits=2),
                'duration': float_round(employee.end_lunch, precision_digits=2)
                
            }
        return response

    # OCC BREAK
    @http.route('/hr_attendance/systray_break_out', type="json", auth="public", csrf=False)
    def user_take_break(self):
        employee = request.env.user.employee_id

        if not employee.is_break:
            employee.is_break = True
        else:
            employee.is_break = False

        # # UPDATE ATTENDANCE TIME IN
        employee._break_action_change()

        return self._get_break_data(employee)

    @http.route('/hr_attendance/take_break', type="json", auth="user")
    def user_break(self):
        employee = request.env.user.employee_id
        return self._get_break_data(employee)

        



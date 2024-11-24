# -*- coding: utf-8 -*-
# Native Python modules
from datetime import datetime, date, time, timedelta

# Local python modules

# Custom python modules

# Odoo modules
from odoo import models, fields, api, _
from odoo.tools.translate import _
from odoo.exceptions import UserError, ValidationError


class HRAttendance(models.Model):
    _inherit = "hr.attendance"

    def _get_check_in(self):
        for rec in self:
            rec.check_in_date = (
                fields.Datetime.context_timestamp(rec, rec.check_in)
                .astimezone(tz)
                .date()
            )

    check_in_date = fields.Date("Date", index=True, compute="_get_check_in", store=True)

    @api.model
    def _cron_update_attendance_sheet(self):
        atd_sheet_obj = self.env["hr.attendance.sheet"]
        atd_sheet = atd_sheet_obj.sudo().search(
            [("date", "=", datetime.now().strftime("%m-%d-%Y"))]
        )
        for x in atd_sheet:
            x.update_attendance_sheet()

    @api.model
    def _cron_create_attendance_sheet(self):
        atd_sheet_obj = self.env["hr.attendance.sheet"]

        # set the day of the week value
        dow_int = int(datetime.now(tz).strftime("%w")) - 1

        if dow_int == -1:
            dow_int = 6

        date_now = datetime.now(tz).strftime("%Y-%m-%d")

        # new! search for employee with active contract and returns employee_id and resource_calendar_id
        query = """
			SELECT 
				main_query.employee_id,
				(
				 CASE main_query.counter 
				 WHEN 1 THEN main_query.temp_id
				 ELSE (
								SELECT 
									resource_calendar_id 
								FROM hr_contract 
								WHERE employee_id = main_query.employee_id AND date_start::DATE <= '%s'::DATE
									AND state in ('open','pending','draft')
								ORDER BY date_start DESC 
								LIMIT 1
							)
					END
				) resource_calendar_id
			FROM 
			(
				SELECT 
					DISTINCT employee_id, count(*) as counter, sum(resource_calendar_id) as temp_id
				FROM hr_contract 
				WHERE 
					state in ('open','pending')
				GROUP BY employee_id
			) as main_query
		""" % (
            date_now
        )

        self._cr.execute(query)
        contract_ids = self._cr.dictfetchall()

        # loop creating of attendance sheet
        if contract_ids:
            for x in contract_ids:

                val = atd_sheet_obj.sudo().search(
                    [
                        ("employee_id", "=", x.get("employee_id")),
                        ("date", "=", datetime.now(tz).strftime("%Y-%m-%d")),
                    ]
                )

                if not val:
                    work_sched = get_attendance_sched(
                        self,
                        date_now,
                        x.get("resource_calendar_id"),
                        get_attendance_sched,
                    )
                    value = {
                        "employee_id": x.get("employee_id"),
                        "date": date_now,
                        "dayofweek": str(dow_int),
                        "planned_in": work_sched.get("planned_in"),
                        "planned_out": work_sched.get("planned_out"),
                    }
                    atd_sheet_obj.create(value)
# -*- coding: utf-8 -*-
# Native Python modules
from datetime import datetime, date, time, timedelta

# Local python modules
import pytz

# Custom python modules

# Odoo modules
from odoo import models, fields, api, _
from odoo.tools.translate import _
from odoo.exceptions import UserError, ValidationError


class Attendance2AttendanceSheet(models.TransientModel):
    _name = "attendance.to.attendance.sheet"

    def create_attendance_sheet(self):
        employee_attendace_obj = self.env["hr.attendance"].search(
            [
                ("pushed_to_sheet", "=", False),
                ("check_in", "!=", False),
                ("check_out", "!=", False),
            ],
            order="check_in_date asc",
        )
        if employee_attendace_obj:
            for data in employee_attendace_obj:
                if data.check_in_date:
                    attendance_sheet = self.env["hr.attendance.sheet"].search(
                        [
                            ("employee_id", "=", data.employee_id.id),
                            ("date", "=", data.check_in_date),
                            ("original", "not in", ["excess", "modified"]),
                        ]
                    )
                    if attendance_sheet:
                        for attendance_vals in attendance_sheet:
                            if attendance_vals:
                                attendance_vals.update_attendance_sheet()
                            else:
                                create_sheet = (
                                    self.env["hr.attendance.sheet"]
                                    .sudo()
                                    .create(
                                        {
                                            "employee_id": data.employee_id.id,
                                            "date": data.check_in_date,
                                        }
                                    )
                                )
                                create_sheet.update_attendance_sheet()
                            data.write({"pushed_to_sheet": True})

    def create_attendance_sheet_daily(self):
        tz = pytz.timezone("Asia/Manila")
        date_now = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")

        attendance_sheet = self.env["hr.attendance.sheet"]

        employee_data = self.env["hr.employee"].search(
            [("contract_id", "!=", False), ("active", "=", True)]
        )

        for employee in employee_data:

            employee_attendance_sheet = self.env["hr.attendance.sheet"].search(
                [("employee_id", "=", employee.id), ("date", "=", date_now)]
            )

            if not employee_attendance_sheet:
                this = attendance_sheet.create(
                    {"employee_id": employee.id, "date": date_now}
                )
                this.update_attendance_sheet()

    def update_attendance_sheet_daily(self):
        tz = pytz.timezone("Asia/Manila")
        date_now = datetime.now(tz).strftime("%Y-%m-%d")
        employee_attendance_sheet = self.env["hr.attendance.sheet"].search(
            [("date", "=", date_now)]
        )
        if employee_attendance_sheet:
            for sheet in employee_attendance_sheet:
                if sheet.original == "original":
                    # print(sheet.employee_id.name)
                    sheet.update_attendance_sheet()

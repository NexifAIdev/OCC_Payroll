# -*- coding: utf-8 -*-
# Native Python modules
from datetime import datetime, date, time, timedelta

# Local python modules

# Custom python modules

# Odoo modules
from odoo import models, fields, api, _
from odoo.tools.translate import _
from odoo.exceptions import UserError, ValidationError


class CustomHolidays(models.Model):
    _name = "custom.holidays"
    _description = "Universal holiday calendar for registered employees."
    _order = "date asc"

    name = fields.Char("Name")
    date = fields.Date("Date")
    state = fields.Selection(
        [("active", "Active"), ("deactive", "Deactive")],
        string="State",
        default="deactive",
    )
    holiday_type = fields.Selection(
        [("regular", "Regular Holiday"), ("special", "Special (Non-Working) Holiday")],
        string="Holiday Type",
        default="regular",
    )
    calendar_id = fields.Many2one("calendar.event", string="Calendar")

    work_location_id = fields.Many2many("hr.work.location", string="Location")

    def cancel_calendar(self):
        """this function deletes the created calendar event upon cancel of holiday"""
        calendar_obj = self.calendar_id
        calendar_obj.unlink()

        self.state = "deactive"

    def push_to_calendar(self):
        """this function creates calendar event linked to this holiday"""

        # CREATE CALENDAR EVENT
        date_start = datetime.strptime(
            self.date.strftime("%Y-%m-%d 00:00:00"), "%Y-%m-%d 00:00:00"
        )
        date_stop = datetime.strptime(
            self.date.strftime("%Y-%m-%d 00:00:00"), "%Y-%m-%d 00:00:00"
        ) + timedelta(hours=23, minutes=59, seconds=59)

        employees = self.env["hr.employee"].search([("user_id", "!=", None)])
        partner = [employee.user_id.partner_id.id for employee in employees]
        partner = self.env["res.partner"].search([("id", "in", partner)])
        calendar = self.env["calendar.event"]

        values = {
            "name": "Holiday : " + self.name,
            "allday": False,
            "start_date": datetime.strptime(self.date.strftime("%Y-%m-%d"), "%Y-%m-%d"),
            "stop_date": datetime.strptime(self.date.strftime("%Y-%m-%d"), "%Y-%m-%d"),
            "start_datetime": date_start - timedelta(hours=8),
            "stop_datetime": date_stop - timedelta(hours=8),
            "start": date_start - timedelta(hours=8),
            "stop": date_stop - timedelta(hours=8),
            "partner_ids": [(6, 0, partner.ids)],
        }
        # c = calendar.create(values)
        # self.calendar_id = c.id
        self.state = "active"

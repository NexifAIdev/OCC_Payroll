# -*- coding: utf-8 -*-
# Native Python modules
from datetime import datetime, date, time, timedelta

# Local python modules

# Custom python modules

# Odoo modules
from odoo import models, fields, api, _
from odoo.tools.translate import _
from odoo.exceptions import UserError, ValidationError


class CustomHolidaysConfig(models.Model):
    _name = "custom.holidays.config"
    _description = "Yearly Holiday Configuration"

    state = fields.Selection(
        [("active", "Active"), ("inactive", "Inactive")], default="active"
    )
    month = fields.Selection(
        [
            ("01", "January"),
            ("02", "February"),
            ("03", "March"),
            ("04", "April"),
            ("05", "May"),
            ("06", "June"),
            ("07", "July"),
            ("08", "August"),
            ("09", "September"),
            ("10", "October"),
            ("11", "November"),
            ("12", "December"),
        ],
        default="01",
    )
    day = fields.Selection(
        [
            ("01", "01"),
            ("02", "02"),
            ("03", "03"),
            ("04", "04"),
            ("05", "05"),
            ("06", "06"),
            ("07", "07"),
            ("08", "08"),
            ("09", "09"),
            ("10", "10"),
            ("11", "11"),
            ("12", "12"),
            ("13", "13"),
            ("14", "14"),
            ("15", "15"),
            ("16", "16"),
            ("17", "17"),
            ("18", "18"),
            ("19", "19"),
            ("20", "20"),
            ("21", "21"),
            ("22", "22"),
            ("23", "23"),
            ("24", "24"),
            ("25", "25"),
            ("26", "26"),
            ("27", "27"),
            ("28", "28"),
            ("29", "29"),
            ("30", "30"),
            ("31", "31"),
        ],
        default="01",
    )

    name = fields.Char("Name")
    holiday_type = fields.Selection(
        [("regular", "Regular Holiday"), ("special", "Special (Non-Working) Holiday")],
        string="Holiday Type",
        default="regular",
    )

    def _cron_create_yearly_holidays(self):
        custom_holiday_obj = self.env["custom.holidays"]
        custom_holiday_config_obj = self.env["custom.holidays.config"]

        holiday_conf_line = custom_holiday_config_obj.sudo().search(
            [("state", "=", "active")]
        )
        hyear = datetime.today().year

        for x in holiday_conf_line:
            hdate = "%s-%s-%s" % (hyear, x.month, x.day)
            values = {"date": hdate, "name": x.name, "holiday_type": x.holiday_type}

            value = custom_holiday_obj.sudo().search([("date", "=", hdate)])

            if not value:
                new_holiday_obj = custom_holiday_obj.create(values)
                # new_holiday_obj.push_to_calendar()

# -*- coding: utf-8 -*-
# Native Python modules

# Local python modules

# Custom python modules

# Odoo modules
from odoo import models, fields, api, _
from odoo.tools.translate import _
from odoo.exceptions import UserError, ValidationError


class HolidaysConfiguration(models.Model):
    _name = "hr.holidays.configuration"
    _snakecased_name = "hr_holidays_configuration"
    _model_path_name = "occ_payroll.model_hr_holidays_configuration"
    _description = "Holidays Configuration"

    day_selection = [(f"{num:02}", f"{num:02}") for num in range(1, 32)]

    name = fields.Char(
        string="Type",
        default=False,
        required=True,
    )

    description = fields.Char(
        string="Description",
        default=False,
        required=True,
    )

    is_ranged = fields.Boolean(
        string="Is ranged?",
        default=False,
    )

    day = fields.Selection(
        selection=day_selection,
        string="Day",
        default=False,
    )

    day_from = fields.Selection(
        selection=day_selection,
        string="Day From",
        default=False,
    )

    day_to = fields.Selection(
        selection=day_selection,
        string="Day To",
        default=False,
    )

    holiday_type = fields.Selection(
        selection=[
            ("regular", "Regular Holiday"),
            ("special", "Special (Non-Working) Holiday"),
        ],
        string="Holiday Type",
        default="regular",
    )

    active = fields.Boolean(
        string="Active",
        default=True,
    )

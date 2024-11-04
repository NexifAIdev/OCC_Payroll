# -*- coding: utf-8 -*-
# Native Python modules

# Local python modules

# Custom python modules

# Odoo modules
from odoo import models, fields, api, _
from odoo.tools.translate import _
from odoo.exceptions import UserError, ValidationError, AccessError


class HrWorkLocationChangeLog(models.Model):
    _name = "hr.work.location.change.log"
    _snakecased_name = "hr_work_location_change_log"
    _model_path_name = "occ_configurations.model_hr_work_location_change_log"
    _description = "Work Location Change Log"
    _order = "create_date desc"

    employee_id = fields.Many2one("hr.employee", string="Employee", required=True)
    old_location = fields.Selection(
        [("onsite", "On-Site"), ("wfh", "Work From Home")], string="Previous Location"
    )
    new_location = fields.Selection(
        [("onsite", "On-Site"), ("wfh", "Work From Home")], string="New Location"
    )
    changed_by = fields.Many2one("res.users", string="Changed By", required=True)
    create_date = fields.Datetime(string="Change Date", readonly=True)

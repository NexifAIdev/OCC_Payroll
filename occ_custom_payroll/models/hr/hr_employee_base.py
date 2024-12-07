# -*- coding: utf-8 -*-
# Native Python modules

# Local python modules

# Custom python modules

# Odoo modules
from odoo import models, fields, api, _
from odoo.tools.translate import _
from odoo.exceptions import UserError, ValidationError

class HrEmployeeBase(models.AbstractModel):
    _inherit = "hr.employee.base"

    # replace work location to a convenient dropdown field
    exhr_work_location = fields.Many2one("hr.work.location", string="Work Location")
    coach_id = fields.Many2one("hr.employee", "Coach", domain="[]")
    parent_id = fields.Many2one("hr.employee", "Manager", domain="[]")
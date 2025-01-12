# -*- coding: utf-8 -*-
# Native Python modules

# Local python modules

# Custom python modules

# Odoo modules
from odoo import models, fields, api, _
from odoo.tools.translate import _
from odoo.exceptions import UserError, ValidationError


class HrEmployeePublic(models.Model):
    _inherit = "hr.employee.public"

    # Fields coming from hr.employee.base
    exhr_work_location = fields.Many2one(readonly=True)
    job_description = fields.Text("Job Description")
    hr_position = fields.Char("HR Position")
    private_address = fields.Text("Address")
    bank_account = fields.Char("Bank Account Number")
    private_phone = fields.Char("Phone")
    email_private = fields.Char("Email")

    analytic_account_id = fields.Many2one(
        "account.analytic.account", "Analytic Account"
    )

    partner_id = fields.Many2one("res.partner", "Partner")
    accounting_tag_id = fields.Many2one("hr.accounting.config")

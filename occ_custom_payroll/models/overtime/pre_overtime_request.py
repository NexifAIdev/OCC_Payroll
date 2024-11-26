# -*- coding: utf-8 -*-
# Native Python modules
from datetime import datetime, date, timedelta

# Local python modules

# Custom python modules

# Odoo modules
from odoo import models, fields, api, _
from odoo.tools.translate import _
from odoo.tools import float_round
from odoo.exceptions import UserError, ValidationError
import odoo.addons.decimal_precision as dp


class PreOvertimeRequest(models.Model):
    _name = "pre.overtime.request"
    _inherit = ["mail.thread"]
    _description = "Pre-Approval Overtime Request"
    
    def _default_employee(self):
        return self.env.context.get("default_employee_id") or self.env[
            "hr.employee"
        ].sudo().search([("user_id", "=", self.env.uid)], limit=1)

    state = fields.Selection(
        selection=lambda self: self.state_list, default="draft", copy=False, track_visibility="onchange"
    )

    name = fields.Char(copy=False, default="New")
    employee_id = fields.Many2one(
        "hr.employee",
        string="Employee Name",
        index=True,
        required=True,
        default=_default_employee,
    )
    department_id = fields.Many2one(
        "hr.department",
        related="employee_id.department_id",
        string="Department",
        readonly=True,
        store=True,
    )

    ot_date = fields.Date(string="OT Date", track_visibility="onchange")
    est_hours = fields.Float(string="Estimated Hours", track_visibility="onchange")
    details = fields.Text(track_visibility="onchange")

    date_filed = fields.Date(string="Date Filed", copy=False)
    date_approved = fields.Date(string="Date Approved", readonly=True, copy=False)

    company_id = fields.Many2one(
        "res.company", related="employee_id.company_id", required=True
    )
    
    preot_policy = fields.Selection(selection=lambda self: self.list_policy, string="OT Policy")
    preapproval_process = fields.Selection(
        selection=lambda self: self.list_approval, string="Pre-OT Approval Process"
    )

    def submit(self):
        approver = 1
        otstage = "pre"
        print(fields.Date.today())
        print(self.ot_date)
        if self.ot_date < fields.Date.today():
            raise UserError("Invalid date for pre-overtime request.")

        if self.preot_policy == "1":
            if self.preapproval_process == "1":
                #'Approver 1 and Approver 2 before it approves'
                self.state = "submitted"
                self.date_filed = fields.Date.today()
                if self.name == "New":
                    self.name = self.env["ir.sequence"].next_by_code(
                        "preovertime_sequence"
                    )

                # email to approver 1
                # self.email_to_coach(email_template='tk_payroll_complete.email_pre_overtime_request')

                # _ot_mail_send(self, self.employee_id.name, self.name, approver, self.id, otstage, self.employee_id.coach_id.name)

            elif self.preapproval_process == "2":
                #'Approver 1 or Approver 2 before it approves'
                self.state = "subver"
                self.date_filed = fields.Date.today()
                if self.name == "New":
                    self.name = self.env["ir.sequence"].next_by_code(
                        "preovertime_sequence"
                    )
                # email to approver 1 and approver 2
                # self.email_to_coach(email_template='tk_payroll_complete.email_pre_overtime_request')
                # self.email_to_manager(email_template='tk_payroll_complete.email_pre_overtime_request')
                # _ot_mail_send(self, self.employee_id.name, self.name, approver, self.id, otstage, self.employee_id.coach_id.name)

            elif self.preapproval_process == "3":
                # Approver 1 only before it approves'
                self.state = "submitted"
                self.date_filed = fields.Date.today()
                if self.name == "New":
                    self.name = self.env["ir.sequence"].next_by_code(
                        "preovertime_sequence"
                    )
                # email to approver 1
                # self.email_to_coach(email_template='tk_payroll_complete.email_pre_overtime_request')
                # _ot_mail_send(self, self.employee_id.name, self.name, approver, self.id, otstage, self.employee_id.coach_id.name)

            elif self.preapproval_process == "4":
                #'Approver 2 only before it approves'),
                self.state = "verified"
                self.date_filed = fields.Date.today()
                if self.name == "New":
                    self.name = self.env["ir.sequence"].next_by_code(
                        "preovertime_sequence"
                    )
                approver = 2
                # email to approver 2
                # self.email_to_manager(email_template='tk_payroll_complete.email_pre_overtime_request')
                # _ot_mail_send(self, self.employee_id.name, self.name, approver, self.id, otstage, self.employee_id.parent_id.name)

            else:
                raise UserError(
                    _("""No valid approval process. Please contact Admin.""")
                )

        else:
            raise UserError(_("""No Need to file Pre-Approval for OT."""))

    def approved_by_1(self):
        if self.preot_policy == "1":
            if self.state == "subver":
                self.state = "approved"
                self.date_approved = fields.Date.today()

            elif self.state == "submitted":
                if self.preapproval_process == "1":
                    #'Approver 1 and Approver 2 before it approves'
                    self.state = "verified"
                    # self.email_to_manager(email_template='tk_payroll_complete.email_pre_overtime_request')

                elif self.preapproval_process == "3":
                    # Approver 1 only before it approves'
                    self.state = "approved"
                    self.date_approved = fields.Date.today()

            else:
                raise UserError(
                    _("""No valid approval process. Please contact Admin.""")
                )

        else:
            raise UserError(_("""No Need to file Pre-Approval for OT."""))

    def approved_by_2(self):
        if self.preot_policy == "1":
            if self.state == "subver":
                self.state = "approved"
                self.date_approved = fields.Date.today()

            elif self.state == "verified":
                self.state = "approved"
                self.date_approved = fields.Date.today()

            else:
                raise UserError(
                    _("""No valid approval process. Please contact Admin.""")
                )

        else:
            raise UserError(_("""No Need to file Pre-Approval for OT."""))

    def reset_to_draft(self):

        if self.state == "cancelled":
            self.state = "draft"

    def set_to_cancel(self):

        if self.state != "approved":
            self.state = "cancelled"

    def set_to_denied_by_1(self):

        if self.state not in ("cancelled", "draft"):
            self.state = "denied"

    def set_to_denied_by_2(self):

        if self.state not in ("cancelled", "draft"):
            self.state = "denied"
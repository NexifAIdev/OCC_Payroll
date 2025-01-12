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


class OvertimeRequest(models.Model):
    _name = "overtime.request"
    _inherit = ["mail.thread", "occ.payroll.cfg"]
    _description = "Overtime Request"

    def _default_employee(self):
        return self.env.context.get("default_employee_id") or self.env[
            "hr.employee"
        ].sudo().search([("user_id", "=", self.env.uid)], limit=1)

    state = fields.Selection(
        selection=lambda self: self.state_list2,
        default="draft",
        copy=False,
        track_visibility="onchange",
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

    date_filed = fields.Date(string="Date Filed", readonly=True, copy=False)
    date_approved = fields.Date(string="Date Approved", readonly=True, copy=False)

    number_of_days = fields.Float(string="Number of Days")

    overtime_line_ids = fields.One2many("overtime.request.line", "overtime_id")

    company_id = fields.Many2one(
        "res.company", related="employee_id.company_id", required=True
    )

    ot_policy = fields.Selection(
        selection=lambda self: self.list_policy, string="OT Policy"
    )
    approval_process = fields.Selection(
        selection=lambda self: self.list_approval, string="OT Approval Process"
    )
    min_ot_hours = fields.Float(string="Minimum OT hours")
    number_of_days = fields.Float(string="Number of Days")
    break_hrs = fields.Float(string="Break Hrs for every straight OT")
    total_hrs_for_brk = fields.Float(string="Straight OT Hrs")

    @api.onchange("employee_id")
    def onchange_employee_id(self):
        dt_today = fields.Date.today()

        data_from = (dt_today - timedelta(days=self.number_of_days)).strftime(
            "%Y-%m-%d"
        )
        date_to = fields.Date.today()

        attsheet_obj = (
            self.env["hr.attendance.sheet"]
            .sudo()
            .search(
                [
                    ("employee_id", "=", self.employee_id.id),
                    ("date", ">=", data_from),
                    ("date", "<=", date_to),
                    ("ot_state", "!=", "processed"),
                ]
            )
        )

    def process_att_sheet(self, sheet_lines, employee_id, state):

        for x in sheet_lines:
            if x.system_generated:
                self.env["hr.attendance.sheet"].sudo().search(
                    [("date", "=", x.date), ("employee_id", "=", employee_id)], limit=1
                ).write({"ot_state": state})

    def process_ot_line(self, ot_lines, state):

        for x in ot_lines:
            if x.status not in ("paid", "denied", "approved"):
                x.status = state

    def submit(self):
        approver = 2
        otstage = "pre"

        for line in self.overtime_line_ids:
            line._check_ot_hours()

        if self.approval_process == "1":
            #'Approver 1 and Approver 2 before it approves'
            self.state = "submitted"
            self.date_filed = fields.Date.today()
            if self.name == "New":
                self.name = self.env["ir.sequence"].next_by_code("overtime_sequence")
            # _ot_mail_send(self, self.employee_id.name, self.name, approver, self.id, otstage, self.employee_id.coach_id.name)
            self.process_att_sheet(
                self.overtime_line_ids, self.employee_id.id, "processed"
            )
            self.process_ot_line(self.overtime_line_ids, "submitted")
            # email approver 1
            # self.email_to_manager(email_template='tk_payroll_complete.email_overtime_request')

        elif self.approval_process == "2":
            #'Approver 1 or Approver 2 before it approves'
            self.state = "subver"
            self.date_filed = fields.Date.today()
            if self.name == "New":
                self.name = self.env["ir.sequence"].next_by_code("overtime_sequence")
            # _ot_mail_send(self, self.employee_id.name, self.name, approver, self.id, otstage, self.employee_id.coach_id.name)
            self.process_att_sheet(
                self.overtime_line_ids, self.employee_id.id, "processed"
            )
            self.process_ot_line(self.overtime_line_ids, "submitted")
            # email approver 1 and approver 2
            # self.email_to_coach(email_template='tk_payroll_complete.email_overtime_request')
            # self.email_to_manager(email_template='tk_payroll_complete.email_overtime_request')

        elif self.approval_process == "3":
            # Approver 1 only before it approves'
            self.state = "submitted"
            self.date_filed = fields.Date.today()
            if self.name == "New":
                self.name = self.env["ir.sequence"].next_by_code("overtime_sequence")
            # _ot_mail_send(self, self.employee_id.name, self.name, approver, self.id, otstage, self.employee_id.coach_id.name)
            self.process_att_sheet(
                self.overtime_line_ids, self.employee_id.id, "processed"
            )
            self.process_ot_line(self.overtime_line_ids, "submitted")
            # email approver 1
            # self.email_to_manager(email_template='tk_payroll_complete.email_overtime_request')

        elif self.approval_process == "4":
            #'Approver 2 only before it approves'),
            self.state = "verified"
            self.date_filed = fields.Date.today()
            if self.name == "New":
                self.name = self.env["ir.sequence"].next_by_code("overtime_sequence")
            # email to approver 2
            # self.email_to_coach(email_template='tk_payroll_complete.email_overtime_request')

            approver = 2
            # _ot_mail_send(self, self.employee_id.name, self.name, approver, self.id, otstage, self.employee_id.parent_id.name)
            self.process_att_sheet(
                self.overtime_line_ids, self.employee_id.id, "processed"
            )
            self.process_ot_line(self.overtime_line_ids, "submitted")

        else:
            raise UserError(_("""No valid approval process. Please contact Admin."""))

    def approved_by_1(self):

        for x in self.overtime_line_ids:
            if x.status == "submitted":
                raise UserError(
                    _(
                        """Please validate OT filed on %s before proceeding."""
                        % (x.date)
                    )
                )

        if self.state == "subver":
            self.state = "approved"
            self.date_approved = fields.Date.today()

        elif self.state == "submitted":
            if self.approval_process == "1":
                #'Approver 1 and Approver 2 before it approves'
                self.state = "verified"
                # email approver 2
                # self.email_to_coach(email_template='tk_payroll_complete.email_overtime_request')

            elif self.approval_process == "3":
                # Approver 1 only before it approves'
                self.state = "approved"
                self.date_approved = fields.Date.today()

        else:
            raise UserError(_("""No valid approval process. Please contact Admin."""))

    def approved_by_2(self):

        for x in self.overtime_line_ids:
            if x.status == "submitted":
                raise UserError(
                    _(
                        """Please validate OT filed on %s before proceeding."""
                        % (x.date)
                    )
                )

        if self.state == "subver":
            self.state = "approved"
            self.date_approved = fields.Date.today()

        elif self.state == "verified":
            self.state = "approved"
            self.date_approved = fields.Date.today()

        else:
            raise UserError(_("""No valid approval process. Please contact Admin."""))

    def reset_to_draft(self):

        if self.state == "cancelled":
            self.state = "draft"
            self.process_ot_line(self.overtime_line_ids, "draft")

    def set_to_cancel(self):

        if self.state != "approved":
            self.state = "cancelled"
            self.process_att_sheet(
                self.overtime_line_ids, self.employee_id.id, "cancelled"
            )
            self.process_ot_line(self.overtime_line_ids, "cancelled")

    def set_to_denied_by_1(self):

        if self.state not in ("cancelled", "draft"):
            self.state = "denied"

    def set_to_denied_by_2(self):

        if self.state not in ("cancelled", "draft"):
            self.state = "denied"

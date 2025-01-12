# -*- coding: utf-8 -*-
# Native Python modules

# Local python modules

# Custom python modules

# Odoo modules
from odoo import models, fields, api, _
from odoo.tools.translate import _
from odoo.exceptions import UserError, ValidationError


class WorkSchedAdjustment(models.Model):
    _name = "work.sched.adjustment"
    _inherit = ["mail.thread", "occ.payroll.cfg"]

    name = fields.Char(copy=False, default="New")
    status = fields.Selection(
        [
            ("draft", "Draft"),
            ("manager", "Manager"),
            ("validate", "Validated"),
            ("cancel", "Cancelled"),
        ],
        copy=False,
        default="draft",
        track_visibility="onchange",
    )

    date_change = fields.Date(string="Date", track_visibility="onchange")
    planned_in = fields.Float(string="Planned In", track_visibility="onchange")
    planned_out = fields.Float(string="Planned Out", track_visibility="onchange")
    reason = fields.Text(string="Reason", track_visibility="onchange")
    employee_id = fields.Many2one(
        "hr.employee",
        string="Employee",
        track_visibility="onchange",
        default=lambda self: self._get_default_requestor(),
        readonly=True,
    )
    company_id = fields.Many2one(
        "res.company", related="employee_id.company_id", required=True
    )

    def action_submit(self):
        self.status = "manager"
        if self.name == "New":
            self.name = self.env["ir.sequence"].next_by_code("work_sched_sequence")

    def action_cancelled_by_manager(self):
        self.status = "cancel"

    def action_cancelled_by_requestor(self):
        self.status = "cancel"

    def action_validate(self):
        self.status = "validate"

        attendance_data = self.env["hr.attendance.sheet"].search(
            [
                ("employee_id", "=", self.employee_id.id),
                ("date", "=", self.date_change),
            ],
            limit=1,
        )

        if attendance_data:
            attendance_data.write(
                {"planned_in": self.planned_in, "planned_out": self.planned_out}
            )
            attendance_data.update_attendance_sheet()

    def reset_to_draft(self):
        self.status = "draft"

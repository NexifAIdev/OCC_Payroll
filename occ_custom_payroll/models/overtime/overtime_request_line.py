# -*- coding: utf-8 -*-
# Native Python modules
from datetime import datetime, date, time, timedelta

# Local python modules

# Custom python modules
from icecream import ic

# Odoo modules
from odoo import models, fields, api, _
from odoo.tools.translate import _
from odoo.exceptions import UserError, ValidationError


class OvertimeRequestLine(models.Model):
    _name = "overtime.request.line"
    _inherit = ["occ.payroll.cfg"]

    def _get_odoo_dow_list(self):
        odoo_dow_list = []
        try:
            odoo_dow_list = self.odoo_dow_list
        except AttributeError as ae:
            odoo_dow_list = self.env["occ.payroll.cfg"].odoo_dow_list

        ic(odoo_dow_list)
        if not len(odoo_dow_list) > 0:
            raise ValidationError(f"occ.payroll.cfg was not loaded properly")

        return odoo_dow_list

    date = fields.Date(default=fields.Date.today(), index=True)
    date_approved = fields.Date(index=True)

    actual_in = fields.Float(string="OT Start", help="Actual Start of OT time.")
    actual_out = fields.Float(string="OT End", help="Actual End of OT time.")
    dayofweek = fields.Selection(
        selection=lambda self: self._get_odoo_dow_list(),
        string="Day of Week",
        index=True,
        default="0",
    )

    payslip_id = fields.Many2one(
        "exhr.payslip", string="Payslip", store=True, index=True
    )

    breakdown_lines = fields.One2many("overtime.breakdown.line", "ot_line_id")

    def _check_ot_hours(self):
        if self.actual_in > self.actual_out:
            raise UserError("Invalid OT Start and OT End.")
        elif self.actual_in == self.actual_out:
            raise UserError("OT Start and OT End cannot be the same.")

        if self.actual_in < 0 or self.actual_in > 24:
            raise UserError("Wrong time input.")

        if self.actual_out < 0 or self.actual_out > 24:
            raise UserError("Wrong time input.")

    @api.depends("actual_in", "actual_out")
    def _compute_total_hrs(self):

        for rec in self:
            deduc = 0.0
            total = rec.actual_out - (rec.actual_in)

            if total > 1:
                if (
                    rec.overtime_id.break_hrs > 0
                    and rec.overtime_id.total_hrs_for_brk > 0
                    and total >= rec.overtime_id.total_hrs_for_brk
                ):
                    deduc = float(
                        int(int(total) / int(rec.overtime_id.total_hrs_for_brk))
                    ) * float(rec.overtime_id.break_hrs)
                rec.total_ot_hrs = total - deduc
            else:
                rec.total_ot_hrs = total

    total_ot_hrs = fields.Float(
        string="Total Hrs", compute="_compute_total_hrs", store=True
    )

    @api.depends("actual_in", "actual_out", "dayofweek", "date", "total_ot_hrs")
    def get_rate_type(self):
        for ln in self:

            dayofWeek = datetime.strptime(str(ln.date), "%Y-%m-%d").weekday()
            config = self.env["payroll.accounting.config"].search([], limit=1)
            if not config:
                raise UserError("Please configure Night Difff Start and End time")
            ns_start = config.default_ns_start
            ns_end = config.default_ns_end

            # rt = get_attedance_type(ln, ln.date, int(dayofWeek), ln.actual_in, ln.actual_out, att.ns_start, att.ns_end,ln.total_ot_hrs)
            rt = self.get_attedance_type(
                ln,
                ln.date,
                int(dayofWeek),
                ln.actual_in,
                ln.actual_out,
                ns_start,
                ns_end,
                ln.total_ot_hrs,
                ln.overtime_id.employee_id.exhr_work_location,
            )
            ln.rate_type = str(rt)

    rate_type = fields.Selection(
        lambda self: self.ratetype_list,
        string="Type",
        store=True,
        compute="get_rate_type",
    )

    details = fields.Text()

    system_generated = fields.Boolean(default=False)

    pre_ot_request_id = fields.Many2one("pre.overtime.request", "Pre-OT Request")

    overtime_id = fields.Many2one(
        "overtime.request", "overtime_line_ids", store=True, index=True
    )
    employee_id = fields.Many2one(
        "hr.employee",
        related="overtime_id.employee_id",
        string="Employee Name",
        index=True,
        store=True,
    )

    status = fields.Selection(
        [
            ("draft", "Draft"),
            ("submitted", "Submitted"),
            ("denied", "Denied"),
            ("verified", "Verified"),
            ("approved", "Approved"),
            ("paid", "Paid"),
            ("cancelled", "Cancelled"),
        ],
        string="Status",
        default="draft",
        index=True,
    )

    company_id = fields.Many2one("res.company", related="overtime_id.company_id")

    # ot_status = fields.Selection(state_list2, related=overtime_id.state)

    @api.onchange("pre_ot_request_id")
    def onchange_pre_ot_request_id(self):
        self.details = self.pre_ot_request_id.details

    def approved_by_1(self):
        if self.overtime_id.state == "subver":
            self.status = "approved"
            self.date_approved = fields.Date.today()

        elif self.overtime_id.state == "submitted":
            if self.overtime_id.approval_process == "1":
                #'Approver 1 and Approver 2 before it approves'

                self.status = "verified"

            elif self.overtime_id.approval_process == "3":
                # Approver 1 only before it approves'
                self.status = "approved"
                self.date_approved = fields.Date.today()

    def approved_by_2(self):
        if self.overtime_id.state == "subver":
            self.status = "approved"
            self.date_approved = fields.Date.today()

        elif self.overtime_id.state == "verified":
            self.status = "approved"
            self.date_approved = fields.Date.today()

        elif self.overtime_id.state == "approved":
            self.status = "approved"
            self.date_approved = fields.Date.today()

    def set_to_denied_by_1(self):
        if self.overtime_id.state not in ("paid"):
            self.status = "denied"

    def set_to_denied_by_2(self):
        if self.overtime_id.state not in ("paid"):
            self.status = "denied"

    def show_breakdown_wizard(self):

        self.ensure_one()

        view = self.env.ref("exhr_payroll_complete.ot_breakdown_form")

        return {
            "name": _("ot.breakdown.form"),
            "type": "ir.actions.act_window",
            "view_type": "form",
            "view_mode": "form",
            "res_model": "overtime.request.line",
            "views": [(view.id, "form")],
            "view_id": view.id,
            "target": "new",
            "res_id": self.id,
        }

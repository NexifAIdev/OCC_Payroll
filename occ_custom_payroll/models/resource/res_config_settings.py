# -*- coding: utf-8 -*-
# Native Python modules
from datetime import datetime, date, time, timedelta

# Local python modules

# Custom python modules
from icecream import ic as ilog

# Odoo modules
from odoo import models, fields, api, _
from odoo.tools.translate import _
from odoo.exceptions import UserError, ValidationError


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    def temp_log(self, output, variable: str = "Not Provided", prefix: str = "occ"):
        self.env["cmd.utilities"].temp_log(output, variable, prefix)

    def _occ_payroll_cfg(self):
        occ_payroll = self.env["occ.payroll.cfg"]
        return {
            "list_policy": occ_payroll.list_policy,
            "list_approval": occ_payroll.list_approval,
        }

    # Attendance sheet
    default_ns_start = fields.Float(
        string="Night Shift Start", default=22, default_model="hr.attendance.sheet"
    )
    default_ns_end = fields.Float(
        string="Night Shift End", default=6, default_model="hr.attendance.sheet"
    )

    # Overtime
    default_preot_policy = fields.Selection(
        selection=lambda self: self._occ_payroll_cfg()["list_policy"],
        string="OT Policy",
        default="2",
        default_model="pre.overtime.request",
    )
    default_preapproval_process = fields.Selection(
        selection=lambda self: self._occ_payroll_cfg()["list_approval"],
        string="Pre-OT Approval Process",
        default="4",
        default_model="pre.overtime.request",
    )

    default_ot_policy = fields.Selection(
        selection=lambda self: self._occ_payroll_cfg()["list_policy"],
        string="OT Policy",
        default="2",
        default_model="overtime.request",
    )  # similar value with default_preot_policy
    default_approval_process = fields.Selection(
        selection=lambda self: self._occ_payroll_cfg()["list_approval"],
        string="OT Approval Process",
        default="4",
        default_model="overtime.request",
    )
    default_min_ot_hours = fields.Integer(
        string="Minimum straight OT hours", default=1, default_model="overtime.request"
    )
    default_number_of_days = fields.Integer(
        string="Numbers of days", default=15, default_model="overtime.request"
    )
    default_break_hrs = fields.Float(
        string="Break Hrs for every straight OT",
        default=0,
        default_model="overtime.request",
    )
    default_total_hrs_for_brk = fields.Float(
        string="Straight OT Hrs", default=0, default_model="overtime.request"
    )

    @api.onchange("default_ot_policy")
    def onchange_default_ot_policy(self):
        if self.default_ot_policy:
            self.default_preot_policy = self.default_ot_policy

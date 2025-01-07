# -*- coding: utf-8 -*-
# Native Python modules
from datetime import datetime, date, time, timedelta

# Local python modules

# Custom python modules

# Odoo modules
from odoo import models, fields, api, _
from odoo.tools.translate import _
from odoo.exceptions import UserError, ValidationError


class HRAttendanceSheet(models.Model):
    _name = "hr.attendance.sheet"
    _inherit = ["occ.payroll.cfg"]
    _description = "Employee Attendance Sheet"
    _order = "date desc, employee_id asc"
    
    employee_id = fields.Many2one("hr.employee", string="Employee", index=True)
    department_id = fields.Many2one(
        related="employee_id.department_id", string="Department", store=True, index=True
    )
    # manager_id = fields.Many2one(related='employee_id.parent_id', string='Manager', store=True, index=True)
    
    attendance_id = fields.Many2one(
        comodel_name="hr.attendance",
        string="Attendance",
        ondelete="cascade",
    )

    date = fields.Date(index=True)
    dayofweek = fields.Selection(selection=lambda self: self.odoo_dow_list, string="Day of Week", index=True, default="0")
    planned_in = fields.Float(
        string="Planned Time In", help="Planned Start time of working."
    )
    planned_out = fields.Float(
        string="Planned Time Out", help="Planned End time of working."
    )
    break_hours = fields.Float(string="Break Hours")
    actual_in = fields.Float(
        string="Actual Time In", help="Actual Start time of working."
    )
    actual_out = fields.Float(
        string="Actual Time Out", help="Actual End time of working."
    )

    actual_time_diff = fields.Float(
        string="Diff(-breaktime)",
        compute="_compute_time_diff",
        help="Actual out - Actual in - Break hours",
    )  # for 48h ww
    hrs_for_payroll = fields.Float("Work Time", compute="_compute_time_diff")

    mins_for_late = fields.Float("Late (mins)")
    mins_for_undertime = fields.Float("Undertime (mins)")

    holiday_amount_pay = fields.Float(string="Holiday Pay")  # FOR CHECKING
    holiday_rate = fields.Float(string="Holiday Rate")  # FOR CHECKING

    rate_type = fields.Selection(selection=lambda self: self.ratetype_list, string="Type")
    schedule_type_ids = fields.Many2many(
        "schedule.type",
        "attendance_sheet_type_rel",
        "sheet_id",
        "type_id",
        string="Status",
    )
    remarks = fields.Text()

    work_schedule_type = fields.Selection(
        [("regular", "Regular"), ("ww", "48H WW"), ("fixed", "Fixed"), ("na", "N/A")],
        track_visibility="onchange",
    )
    company_id = fields.Many2one(
        "res.company", readonly=True, related="employee_id.company_id"
    )

    original = fields.Selection(
        [("original", "Original"), ("excess", "Excess"), ("modified", "Modified")],
        default="original",
    )
    extra = fields.Boolean("Extra")
    active = fields.Boolean("Active", default=True)
    manager_ids = fields.Many2many(
        "res.users", compute="_compute_manager_ids", store=True
    )

    # UNUSED FIELDS - START
    leave_start = fields.Float(
        string="Paid Leave Start", help="Start time of paid leave."
    )
    leave_end = fields.Float(
        string="Paid Leave End", help="End End time of paid leave."
    )
    time_diff = fields.Float(string="Work Time")
    hrs_for_holiday = fields.Float("Total Hrs - Holiday")
    hrs_for_leave = fields.Float("Total Hrs - Leave")
    hrs_for_overtime = fields.Float("Total Hrs - Overtime")
    ww_hours = fields.Float("WW Hours")
    ww_hours_absent = fields.Float("WW Hours Absent")
    tardy_mins = fields.Float(string="Tardy (min)", help="Computed tardy in minutes")
    undertime_mins = fields.Float(
        string="Undertime (min)", help="Computed  undertime in minutes"
    )
    nd_hours = fields.Float(
        string="Night Differential Hours"
    )  # work during 10pm to 6am PHT
    leave_amount_pay = fields.Float(string="Leave Pay")
    nightdiff_amount_pay = fields.Float(string="Night Diff. Pay")
    ot_state = fields.Selection(
        [("draft", "Draft"), ("processed", "Processed"), ("cancelled", "Cancelled")],
        default="draft",
    )
    # UNUSED FIELDS - END

    ns_start = fields.Float(string="Night Shift Start")
    ns_end = fields.Float(string="Night Shift End")
    
    payslip_id = fields.Many2one("exhr.payslip", string="Payslip", store=True, index=True)

    # overtime_amount_pay = fields.Float(string='Overtime Pay')
    # nightdiff_amount_pay = fields.Float(string='Night Diff. Pay')
    # holiday_amount_pay = fields.Float(string='Holiday Pay')

    tardiness_amount_ded = fields.Float(string="Tardiness Deduction")
    undertime_amount_ded = fields.Float(string="Undertime Deduction")
    leavewopay_amount_ded = fields.Float(string="Leave Deduction")
    
    @api.constrains("attendance_id")
    def _check_unique_attendance(self):
        for record in self:
            if record.attendance_id and self.search_count([("attendance_id", "=", record.attendance_id.id)]) > 1:
                raise ValidationError("Each Attendance can only have one Attendance Sheet.")
    
    @api.depends("employee_id", "actual_in", "actual_out")
    def _compute_manager_ids(self):
        for rec in self:
            rec.manager_ids = (
                rec.env["hr.employee"]
                .search([("id", "=", rec.employee_id.id)])
                .parent_id.user_id
            )
            manager1 = (
                rec.env["hr.employee"]
                .search([("id", "=", rec.employee_id.id)])
                .parent_id
            )
            manager2 = manager1.parent_id
            if manager2:
                rec.manager_ids = [(4, manager2.user_id.id)]
                manager3 = manager2.parent_id

                if manager3:
                    rec.manager_ids = [(4, manager3.user_id.id)]
                    manager4 = manager3.parent_id
                    if manager4:
                        rec.manager_ids = [(4, manager4.user_id.id)]

    @api.onchange("date")
    def onchange_date(self):
        if self.date:
            dow_int = self.date.weekday()
            if dow_int == -1:
                dow_int = 6
            self.dayofweek = str(dow_int)

    def _compute_time_diff(self):
        """Computes the actual_time_diff and hrs_for_payroll
        - actual_time_diff - used for 48HWW
        - hrs_for_payroll - used for REGULAR
        """
        for rec in self:
            actual_time_diff = 0
            hrs_for_payroll = 0
            # actual_time_diff

            if rec.actual_in and rec.actual_out:  # with attendance
                actual_time_diff = rec.actual_out - rec.actual_in - rec.break_hours
                if (
                    rec.actual_out - rec.actual_in <= 5
                ):  # half-day, without breakhours deduction
                    actual_time_diff = rec.actual_out - rec.actual_in

            # hrs_for_payroll
            if rec.planned_in and rec.planned_out and rec.actual_in and rec.actual_out:
                actual_in_biased = rec.actual_in
                if rec.actual_in < rec.planned_in:
                    actual_in_biased = rec.planned_in

                actual_out_biased = rec.actual_out
                if rec.actual_out > rec.planned_out:
                    actual_out_biased = rec.planned_out

                hrs_for_payroll = actual_out_biased - actual_in_biased - rec.break_hours
                if (
                    actual_out_biased - actual_in_biased < 5
                ):  # half-day, without breakhours deduction
                    hrs_for_payroll = actual_out_biased - actual_in_biased

            # write values to field
            rec.actual_time_diff = actual_time_diff
            rec.hrs_for_payroll = hrs_for_payroll

    def update_attendance_sheet(self):
        undertime = 0

        # Update Day of Week
        self.onchange_date()

        contract = self.env["hr.contract"].search(
            [
                ("employee_id", "=", self.employee_id.id),
                ("state", "=", "open"),
                ("date_start", "<=", self.date),
            ],
            limit=1,
        )
        if contract:
            # Update Work Schedule Type
            self.work_schedule_type = contract.work_schedule_type

            # Update Planned In and Planned Out - START
            work_sched = self.get_attendance_sched(
                self.date,
                contract.resource_calendar_id,
                self.employee_id.exhr_work_location,
            )

            self.planned_in = work_sched.get("planned_in")
            self.planned_out = work_sched.get("planned_out")
            self.break_hours = work_sched.get("break_hours")
            # Update Planned In and Planned Out - END

            # Update Night Differential - START // FOR CHECKING - should remove this?
            config = self.env["payroll.accounting.config"].search([], limit=1)
            if not config:
                raise UserError("Please configure Night Difff Start and End time")
            ns_start = config.default_ns_start
            ns_end = config.default_ns_end
            # Update Night Differential - END

            # Update Type
            self.rate_type = str(
                self.get_attendance_type(
                    self.date,
                    int(self.dayofweek),
                    self.planned_in,
                    self.planned_out,
                    self.actual_in,
                    self.actual_out,
                    ns_start,
                    ns_end,
                    self.employee_id.exhr_work_location,
                )
            )

            # Update Actual In and Actual Out
            actual_att = self.get_attendance_actual()

            # Update holiday amount pay - START //FOR CHECKING - should remove this? check first the computation in payslip
            if self.work_schedule_type == "regular" or self.work_schedule_type == "ww":
                emp_contract = self.env["hr.contract"].search(
                    [
                        ("employee_id", "=", self.employee_id.id),
                        ("state", "in", ["open"]),
                    ],
                    order="id desc",
                    limit=1,
                )
                holiday_rate_type_list = [
                    2,
                    4,
                    6,
                    10,
                    12,
                    14,
                    18,
                    20,
                    22,
                    26,
                    28,
                    30,
                    3,
                    5,
                    7,
                    11,
                    13,
                    15,
                    19,
                    21,
                    23,
                    27,
                    29,
                    31,
                ]
                if int(self.rate_type) in holiday_rate_type_list:
                    t = dict(self._fields["rate_type"].selection).get(self.rate_type)
                    rate_table = self.env["overtime.rate.config"].search(
                        [("name", "=", t)]
                    )

                    self.holiday_amount_pay = (
                        self.hrs_for_holiday
                        * emp_contract.hourly_rate
                        * (rate_table.percentage - 1)
                    )
                    self.holiday_rate = rate_table.percentage
            # Update holiday amount pay - END

            # Update Status - START
            self.schedule_type_ids = [(5, 0, 0)]  # new way to clear many2many
            work_hr = self.planned_out - self.planned_in - self.break_hours
            half_work_hr = work_hr / 2  # FOR CHECKING - can this be eliminated?
            status = self.get_attendance_status(
                self.date,
                work_hr,
                half_work_hr,
                self.planned_in,
                self.planned_out,
                self.actual_in,
                self.actual_out,
                self.work_schedule_type,
                self.rate_type,
                self.employee_id.exhr_work_location,
            )

            if status:
                self.schedule_type_ids = [(6, 0, [status])]
            # Update Status - END

            # Update Remarks
            self.remarks = self.get_attendance_remarks(
                self.employee_id, self.date, self.date
            )

            # Update Tardiness (mins)
            self.mins_for_late = self.get_mins_for_late(self)

            # Update Undertime (mins)
            self.mins_for_undertime = self.get_mins_for_undertime(
                work_hr, half_work_hr
            )

            # recompute the Planned In and Planned Out of Employees if Holiday
            holiday_status = self.get_holiday_status(
                self.date, self.employee_id.exhr_work_location
            )
            if holiday_status.get("count") > 0:
                self.planned_in = 0
                self.planned_out = 0

            # recompute the Planned In and Planned Out of Employees if NOT Regular working schedule
            if self.work_schedule_type != "regular":
                self.planned_in = 0
                self.planned_out = 0
        else:
            exp_contract = self.env["hr.contract"].search(
                [
                    ("employee_id", "=", self.employee_id.id),
                    ("date_start", "<=", self.date),
                    ("date_end", ">=", self.date),
                ],
                limit=1,
            )
            if exp_contract:
                self.work_schedule_type = exp_contract.work_schedule_type

                # Update Planned In and Planned Out - START
                work_sched = self.get_attendance_sched(
                    self.date,
                    exp_contract.resource_calendar_id,
                    self.employee_id.exhr_work_location,
                )

                self.planned_in = work_sched.get("planned_in")
                self.planned_out = work_sched.get("planned_out")
                self.break_hours = work_sched.get("break_hours")
                # Update Planned In and Planned Out - END

                # Update Night Differential - START // FOR CHECKING - should remove this?
                config = self.env["payroll.accounting.config"].search([], limit=1)
                if not config:
                    raise UserError("Please configure Night Difff Start and End time")
                ns_start = config.default_ns_start
                ns_end = config.default_ns_end
                # Update Night Differential - END

                # Update Type
                self.rate_type = str(
                    self.get_attendance_type(
                        self.date,
                        int(self.dayofweek),
                        self.planned_in,
                        self.planned_out,
                        self.actual_in,
                        self.actual_out,
                        ns_start,
                        ns_end,
                        self.employee_id.exhr_work_location,
                    )
                )

                # Update Actual In and Actual Out
                actual_att = self.get_attendance_actual()

                # Update holiday amount pay - START //FOR CHECKING - should remove this? check first the computation in payslip
                if (
                    self.work_schedule_type == "regular"
                    or self.work_schedule_type == "ww"
                ):
                    holiday_rate_type_list = [
                        2,
                        4,
                        6,
                        10,
                        12,
                        14,
                        18,
                        20,
                        22,
                        26,
                        28,
                        30,
                        3,
                        5,
                        7,
                        11,
                        13,
                        15,
                        19,
                        21,
                        23,
                        27,
                        29,
                        31,
                    ]
                    if int(self.rate_type) in holiday_rate_type_list:
                        t = dict(self._fields["rate_type"].selection).get(
                            self.rate_type
                        )
                        rate_table = self.env["overtime.rate.config"].search(
                            [("name", "=", t)]
                        )

                        self.holiday_amount_pay = (
                            self.hrs_for_holiday
                            * exp_contract.hourly_rate
                            * (rate_table.percentage - 1)
                        )
                        self.holiday_rate = rate_table.percentage
                # Update holiday amount pay - END

                # Update Status - START
                self.schedule_type_ids = [(5, 0, 0)]  # new way to clear many2many
                work_hr = self.planned_out - self.planned_in - self.break_hours
                half_work_hr = work_hr / 2  # FOR CHECKING - can this be eliminated?
                status = self.get_attendance_status(
                    self.date,
                    work_hr,
                    half_work_hr,
                    self.planned_in,
                    self.planned_out,
                    self.actual_in,
                    self.actual_out,
                    self.work_schedule_type,
                    self.rate_type,
                    self.employee_id.exhr_work_location,
                )

                if status:
                    self.schedule_type_ids = [(6, 0, [status])]
                # Update Status - END

                # Update Remarks
                self.remarks = self.get_attendance_remarks(
                    self.employee_id, self.date, self.date
                )

                # Update Tardiness (mins)
                self.mins_for_late = self.get_mins_for_late(self)

                # Update Undertime (mins)
                self.mins_for_undertime = self.get_mins_for_undertime(
                    work_hr, half_work_hr
                )

                # get updated in and out from attendance correction
                print("here")
                attendance_correction = self.env["manual.attendance"].search(
                    [
                        ("employee_id", "=", self.employee_id.id),
                        ("name", "=", self.date),
                        ("status", "=", "validate"),
                    ],
                    order="create_date desc",
                    limit=1,
                )
                if attendance_correction:
                    if attendance_correction.attendance_type == "out":
                        self.actual_out = attendance_correction.date_to
                    elif attendance_correction.attendance_type == "in_out":
                        self.actual_in = attendance_correction.date_from
                        self.actual_out = attendance_correction.date_to

                # get updated work schedule

                # recompute the Planned In and Planned Out of Employees if Holiday
                holiday_status = self.get_holiday_status(
                    self.date, self.employee_id.exhr_work_location
                )
                if holiday_status.get("count") > 0:
                    self.planned_in = 0
                    self.planned_out = 0

                # recompute the Planned In and Planned Out of Employees if NOT Regular working schedule
                if self.work_schedule_type != "regular":
                    self.planned_in = 0
                    self.planned_out = 0
# -*- coding: utf-8 -*-
# Native Python modules
from datetime import datetime, date, timedelta

# Local python modules

# Custom python modules
from icecream import ic

# Odoo modules
from odoo import models, fields, api, _
from odoo.tools.translate import _
from odoo.tools import float_round
from odoo.exceptions import UserError, ValidationError
import odoo.addons.decimal_precision as dp


class exhr_payslip(models.Model):
    _name = "exhr.payslip"
    _description = "Employee's Payslip"
    _inherit = ["mail.thread", "mail.activity.mixin", "occ.payroll.cfg"]

    name = fields.Char(
        "Payslip No.", copy=False, track_visibility="onchange", default="Draft"
    )
    employee_id = fields.Many2one(
        "hr.employee",
        string="Employee's Name",
        required=True,
        index=True,
        track_visibility="onchange",
    )
    department_id = fields.Many2one(
        related="employee_id.department_id", string="Department", store=True, index=True
    )
    state = fields.Selection(
        [("draft", "Draft"), ("posted", "Posted"), ("cancel", "Cancel")],
        copy=False,
        default="draft",
        track_visibility="onchange",
    )
    id_number = fields.Char(string="I.D. No.", track_visibility="onchange")
    pay_period_from = fields.Date(
        string="Pay period from", index=True, track_visibility="onchange"
    )
    pay_period_to = fields.Date(
        string="Pay period to", index=True, track_visibility="onchange"
    )
    cutoff_date = fields.Date(string="Payout Date")
    posted_date = fields.Date()

    earnings_line_ids = fields.One2many("exhr.payslip.earnings", "payslip_id")
    deductions_line_ids = fields.One2many("exhr.payslip.deductions", "payslip_id")
    nontaxable_line_ids = fields.One2many("exhr.payslip.nontaxable", "payslip_id")
    attendance_sheet_ids = fields.One2many("hr.attendance.sheet", "payslip_id")

    overtime_ids = fields.One2many("overtime.request.line", "payslip_id")
    leave_ids = fields.One2many("payslip.leave.line", "payslip_id")

    sss_ids = fields.One2many("sss.contribution.line", "payslip_id")
    phic_ids = fields.One2many("phic.contribution.line", "payslip_id")
    hdmf_ids = fields.One2many("hdmf.contribution.line", "payslip_id")

    company_id = fields.Many2one(
        "res.company", default=lambda self: self.env.company, required=True
    )

    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
        default=lambda self: self.env.user.company_id.currency_id,
        track_visibility="always",
    )

    company_currency_id = fields.Many2one(
        "res.currency",
        related="company_id.currency_id",
        string="Company Currency",
        readonly=True,
    )

    # footer total
    amount_basic_salary = fields.Monetary(
        string="Base Salary",
        store=True,
        compute="_compute_basic",
        readonly=True,
        track_visibility="always",
    )
    amount_untaxed = fields.Monetary(
        string="Taxable Amount",
        store=True,
        compute="_compute_amount",
        readonly=True,
        track_visibility="always",
    )
    amount_nontaxable_signed = fields.Monetary(
        string="Non-Taxable Amount - Old",
        store=True,
        compute="_compute_amount",
        readonly=True,
        track_visibility="always",
    )
    amount_tax_signed = fields.Monetary(
        string="Tax Withheld Amount",
        store=True,
        compute="_compute_amount",
        readonly=True,
        track_visibility="always",
    )
    amount_total = fields.Monetary(
        string="Net Pay",
        store=True,
        compute="_compute_amount",
        readonly=True,
        track_visibility="always",
    )
    new_amount_nontaxable = fields.Monetary(
        string="Non-Taxable Amount",
        store=True,
        compute="_compute_amount",
        readonly=True,
        track_visibility="always",
    )

    move_id = fields.Many2one("account.move")

    # hours/days fields
    total_working_days = fields.Float(
        "Total Working Days", compute="_compute_total_working_days", store=False
    )
    total_holidays = fields.Float(
        "Total Holidays", compute="_compute_total_working_days"
    )  # only for view, not included in computations
    hrs_for_prorate = fields.Float(
        "Hrs(for pro-rate)", compute="_compute_hrs_for_prorate"
    )
    no_days_present = fields.Float()

    # UNUSED FIELDS - START
    no_days_holiday_present = fields.Float()
    no_hrs_ot = fields.Float()
    # UNUSED FIELDS - END

    payroll_id = fields.Many2one(
        "exhr.payroll", string="Reference", store=True, ondelete="cascade", index=True
    )

    def _compute_total_working_days(self):
        # Computes the total_working_days, total_holidays
        for rec in self:
            count_work_days = 0
            count_holidays = 0

            contract = self.env["hr.contract"].search(
                [
                    ("employee_id", "=", rec.employee_id.id),
                    ("state", "=", "open"),
                    ("date_start", "<=", rec.cutoff_date),
                ],
                limit=1,
            )

            if contract:
                for i in range((rec.pay_period_to - rec.pay_period_from).days + 1):
                    date = rec.pay_period_from + timedelta(days=i)

                    c = rec.get_count_work_days(
                        date, int(date.weekday()), rec.employee_id.exhr_work_location
                    )
                    count_work_days += c

                    a = self.get_holiday_pay(
                        date,
                        int(date.weekday()),
                        rec.employee_id.exhr_work_location,
                        contract,
                    )
                    count_holidays += a

            rec.total_holidays = count_holidays
            rec.total_working_days = count_work_days

    def _compute_hrs_for_prorate(self):
        # Computes the hrs_for_prorate for REGULAR and 48H WW
        for rec in self:
            hrs = 0
            # extra_hrs = 0
            # vals = self.env['hr.contract'].search([('employee_id','=',rec.employee_id.id),('state','=','open'),('date_start','<=',rec.cutoff_date)],limit=1)
            att_list = self.env["hr.attendance.sheet"].search(
                [("employee_id", "=", rec.employee_id.id), ("payslip_id", "=", rec.id)]
            )

            absent_days = rec.total_working_days - rec.no_days_present

            if att_list:
                work_sched = att_list[0].work_schedule_type

                mins = sum([a.mins_for_undertime + a.mins_for_late for a in att_list])
                total_hrs = (rec.total_working_days * 8) - (mins / 60)

                if work_sched == "regular":
                    hrs = total_hrs - absent_days * 8
                    actual_time_diff = sum([a.actual_time_diff for a in att_list])
                    if hrs > actual_time_diff:
                        hrs = actual_time_diff
                    # if not vals.daily_wage:
                    # 	for rec in att_list:
                    # 		if rec.rate_type in [('2','3','10','11','18','19','26','27')] and rec.actual_time_diff>0:
                    # 			if rec.actual_time_diff > 8:
                    # 				extra_hrs += 8
                    # 			else:
                    # 				extra_hrs += rec.actual_time_diff

                elif work_sched == "ww":
                    for a in att_list:
                        if a.actual_time_diff > 10:
                            hrs += 10
                        else:
                            hrs += a.actual_time_diff

                if hrs > (rec.total_working_days * 8):
                    hrs = rec.total_working_days * 8

            rec.hrs_for_prorate = hrs

    def compute_count_days(self, vals):
        """Compute the number of days the employee is present for the payroll period (no_days_present)
        - REGULAR, 48HWW, FIXED, DAILY WAGE EARNER, NOT DAILY WAGE EARNER
        """
        # hol_count = 0
        # days_present - used for NOT daily wage earner, REGULAR Working Sched- computes all days present
        days_present = self.env["hr.attendance.sheet"].search_count(
            [
                ("actual_in", ">", 0),
                ("actual_out", ">", 0),
                ("payslip_id", "=", self.id),
                ("employee_id", "=", self.employee_id.id),
            ]
        )
        ic(days_present)

        # days_present_daily_wage - used for daily wage earner - computes all days present , NOT including holidays
        days_present_daily_wage = self.env["hr.attendance.sheet"].search_count(
            [
                ("actual_in", ">", 0),
                ("actual_out", ">", 0),
                ("payslip_id", "=", self.id),
                ("employee_id", "=", self.employee_id.id),
                ("schedule_type_ids", "not in", (7)),
            ]
        )
        ic(days_present_daily_wage)

        # days_present_fixed - used for FIXED and 48H WW working sched - computes all days present on Ordinary Days ONLY
        days_present_fixed = self.env["hr.attendance.sheet"].search_count(
            [
                ("actual_in", ">", 0),
                ("actual_out", ">", 0),
                ("payslip_id", "=", self.id),
                ("employee_id", "=", self.employee_id.id),
                ("rate_type", "=", "0"),
            ]
        )
        ic(days_present_fixed)

        # att_list = self.env['hr.attendance.sheet'].search([('actual_in','>',0),('actual_out','>',0),
        # 											('payslip_id','=',self.id),('employee_id','=',self.employee_id.id)])

        days_present_regular = self.env["hr.attendance.sheet"].search_count(
            [
                ("actual_in", ">", 0),
                ("actual_out", ">", 0),
                ("payslip_id", "=", self.id),
                ("employee_id", "=", self.employee_id.id),
                ("schedule_type_ids", "not in", (7)),
                ("rate_type", "not in", (2, 3, 10, 11, 18, 19, 26, 27)),
            ]
        )
        ic(days_present_regular)
        # for rec in att_list:
        # 	if '7' in rec.schedule_type_ids.ids: #holiday
        # 		hol_count +=1

        ic(vals)
        if vals.daily_wage:
            # print(days_present_daily_wage)
            self.no_days_present = days_present_daily_wage

            # print('days_present_daily_wage : ', days_present_daily_wage)
        elif (vals.work_schedule_type == "regular") and not vals.daily_wage:
            self.no_days_present = days_present_regular

        elif (
            vals.work_schedule_type == "fixed" or vals.work_schedule_type == "ww"
        ) and not vals.daily_wage:
            self.no_days_present = days_present_regular

        # print('self.no_days_present : ', self.no_days_present)

    @api.depends(
        "earnings_line_ids.amount_subtotal", "deductions_line_ids.amount_total"
    )
    def _compute_basic(self):
        """amount_basic_salary = sum of all earnings_line_ids as per AVSC policy"""
        for rec in self:
            basic_amt = sum(line.amount_subtotal for line in rec.earnings_line_ids)
            rec.amount_basic_salary = basic_amt

    @api.depends(
        "earnings_line_ids.amount_subtotal",
        "deductions_line_ids.amount_total",
        "nontaxable_line_ids.amount_total",
    )
    def _compute_amount(self):
        """
        Computes the following fields:
        - amount_untaxed - Taxable Income in view - based on this formula: all earnings - all deductions + taxable allowance
        - amount_nontaxable_signed - Nontaxable income field  (not seen in view) - sum of all nontaxble line in allowances, including the loans
        - amount_tax_signed - Withholding Tax field - tax deduction from the withholding tax table (basis: higher amount base salary vs taxable_amt)
        - amount_total - Net Pay field
        - new_amount_nontaxable - Nontaxable income field (seen in view) - sum of all nontaxble line in allowances, NOT including the loans
        """
        for rec in self:
            base_taxable = 0
            round_curr = rec.currency_id.round
            contract = self.env["hr.contract"].search(
                [("employee_id", "=", rec.employee_id.id), ("state", "in", ["open"])]
            )

            if contract:
                base_taxable = contract.wage
                if contract.payroll_type_id.name == "Semi-Monthly":
                    base_taxable = contract.wage / 2

            taxable_amt = sum(
                line.amount_subtotal for line in rec.earnings_line_ids
            ) - sum(
                line.amount_total for line in rec.deductions_line_ids
            )  # all earnings less all deductions
            taxable_allowance = self.env["exhr.payslip.nontaxable"].search(
                [("payslip_id", "=", rec.id), ("taxable", "=", True)]
            )  # all taxable allowance

            if taxable_allowance:
                allowance_amt = sum(
                    line.amount_total for line in taxable_allowance
                )  # sum of all taxable allowance
                taxable_amt = (
                    taxable_amt + allowance_amt
                )  # all earnings - all deductions + taxable allowance

            taxable_amt0 = taxable_amt

            # taxable_amt should always get the higher amount (as per AVSC policy)
            if (
                base_taxable > taxable_amt
            ):  # check if computed (all earnings - all deductions + taxable allowance) is less than contract semi-monthly wage
                taxable_amt = base_taxable

            # writing of values to the fields
            if rec.payroll_id.for_13th_mo == False:
                rec.amount_tax_signed = rec.compute_tax(taxable_amt) * -1
            else:
                rec.amount_tax_signed = 0
            rec.amount_untaxed = taxable_amt0
            rec.amount_nontaxable_signed = sum(
                line.amount_total
                for line in rec.nontaxable_line_ids
                if not line.taxable
            )
            rec.amount_total = (
                taxable_amt0 + rec.amount_tax_signed + rec.amount_nontaxable_signed
            )  # Net Pay
            rec.new_amount_nontaxable = sum(
                line.amount_total
                for line in rec.nontaxable_line_ids
                if line.taxable != True and not line.loan_id
            )

    def compute_base_salary(self, vals):
        """Compute of Base Pay in Earnings table:
        - Contract - Daily Wage Earner (daily_wage = TRUE)
            - Base Salary = No. of Days present * Daily Rate
            - If 48H WW: Base Salary = Total Working Days * Daily Rate
        - Contract - NOT Daily Wage Earner (daily_wage = FALSE)
            - Semi-monthly (AVSC has only Semi-monthly employees)
            - Base Salary = Monthly Salary / 2 (wage/2)
        """
        if vals:
            att_list = self.env["hr.attendance.sheet"].search(
                [
                    ("employee_id", "=", self.employee_id.id),
                    ("payslip_id", "=", self.id),
                ]
            )
            ic(att_list)
            no_days_present = self.no_days_present
            ic(no_days_present)

            if (
                self.env["earnings.type"].search_count(
                    [("name", "=", "Base Salary"), ("active", "=", True)]
                )
                > 0
            ):
                val_str = vals.payroll_type_id.name
                ic(val_str)

                earning_id = self.env["earnings.type"].search(
                    [("name", "=", "Base Salary"), ("active", "=", True)], limit=1
                )
                ic(earning_id)
                amount = 0
                no_day_hrs_disp = ""
                if vals.daily_wage:
                    for rec in att_list:
                        if (
                            "2" in rec.schedule_type_ids.ids
                            and rec.actual_time_diff > 0
                        ):  # on leave half day
                            no_days_present -= 0.5

                    amount = no_days_present * vals.daily_rate
                    no_day_hrs_disp = (
                        str(round(no_days_present, 2)) + " Days"
                        if no_days_present
                        else ""
                    )

                    if (
                        vals.work_schedule_type == "ww"
                    ):  # 48H WW: deductions for the days that employee is absent is considered in Undertime deduction
                        amount = self.total_working_days * vals.daily_rate
                        no_day_hrs_disp = ""

                else:  # if NOT daily wage earner
                    no_day_hrs_disp = ""
                    if vals.payroll_type_id.name == "Monthly":
                        amount = vals.wage

                    elif vals.payroll_type_id.name == "Semi-Monthly":
                        amount = vals.wage / 2

                ic(amount)
                ic(no_day_hrs_disp)
                if (
                    vals.work_schedule_type == "fixed"
                    or vals.work_schedule_type == "na"
                ):
                    amount = vals.wage / 2

                if amount > 0:
                    count = self.env["exhr.payslip.earnings"].search_count(
                        [("payslip_id", "=", self.id), ("name_id", "=", earning_id.id)]
                    )
                    ic(count)

                    if count == 0:  # nothing found, will create earnings line
                        self.env["exhr.payslip.earnings"].create(
                            {
                                "payslip_id": self.id,
                                "name_id": earning_id.id,
                                "amount_subtotal": amount,
                                "no_day_hrs_disp": no_day_hrs_disp,
                            }
                        )

                    else:  # existing found, will update the existing amount
                        self.env["exhr.payslip.earnings"].search(
                            [
                                ("payslip_id", "=", self.id),
                                ("name_id", "=", earning_id.id),
                            ]
                        ).write(
                            {
                                "amount_subtotal": amount,
                                "no_day_hrs_disp": no_day_hrs_disp,
                            }
                        )

            else:
                raise UserError("No Base Salary found on earnings configuration.")

        else:
            raise UserError("No Running Contract found!")

    def compute_overtime(self, vals):
        """Compute of Overtime in Earnings table:
        // FOR CHECKING
        """
        if vals:
            # UPDATE - 07/17/20
            ot_lines_1 = self.env["overtime.request.line"].search(
                [
                    ("date", ">=", self.pay_period_from),
                    ("date", "<=", self.pay_period_to),
                    ("employee_id", "=", self.employee_id.id),
                    ("status", "=", "approved"),
                ]
            )
            ot_lines_2 = self.env["overtime.request.line"].search(
                [
                    ("date", "<", self.pay_period_from),
                    ("employee_id", "=", self.employee_id.id),
                    ("status", "=", "approved"),
                ]
            )
            ot_lines = ot_lines_1 + ot_lines_2

            no_day_hrs = 0
            sunday_no_day_hrs = 0
            ot_brkdwn = []
            # Replace the old OT BREAKDOWN
            for ot in ot_lines:
                old_list = self.env["overtime.breakdown.line"].search(
                    [("ot_line_id", "=", ot.id)]
                )
                for ln in old_list:
                    ln.unlink()

            for ot in ot_lines:
                ot.payslip_id = self.id
                has_nd = False
                if ot.date.weekday() == 6:
                    no_day_hrs += ot.total_ot_hrs
                else:
                    no_day_hrs += ot.total_ot_hrs

                rt = (
                    self.env["overtime.rate.config"]
                    .search([("rate_id", "=", ot.rate_type)])
                    .percentage
                )
                nd_rate = (
                    self.env["overtime.rate.config"]
                    .search([("rate_id", "=", 8)])
                    .percentage
                )
                hourly_rate = vals.hourly_rate * rt

                # Night Diff
                if int(ot.rate_type) in (
                    8,
                    9,
                    10,
                    11,
                    12,
                    13,
                    14,
                    15,
                    24,
                    25,
                    26,
                    27,
                    28,
                    29,
                    30,
                    31,
                ):
                    has_nd = True
                    hourly_rate = hourly_rate / nd_rate
                    rt = rt / nd_rate  # -10% for separate computation

                # Ordinary day with OT (by default)
                if ot.rate_type in ("0", "8", "16", "24"):
                    # Ordinary Overtime
                    vals2 = {
                        "ot_line_id": ot.id,
                        "date": ot.date,
                        "rate_type": ot.rate_type,
                        "rate": rt,
                        "hours": ot.total_ot_hrs,
                        "hourly_rate": hourly_rate,
                    }
                    ot_brkdwn.append(vals2)

                # WITH HOLIDAY
                elif ot.rate_type in (
                    "4",
                    "5",
                    "12",
                    "13",
                    "20",
                    "21",
                    "28",
                    "29",
                    "2",
                    "3",
                    "10",
                    "11",
                    "18",
                    "19",
                    "26",
                    "27",
                    "6",
                    "7",
                    "14",
                    "15",
                    "22",
                    "23",
                    "30",
                    "31",
                ):

                    if ot.rate_type in (
                        "18",
                        "19",
                        "20",
                        "21",
                        "22",
                        "23",
                        "26",
                        "27",
                        "28",
                        "29",
                        "30",
                        "31",
                    ):

                        # dbl checking
                        if ot.total_ot_hrs > 8:
                            # SAMPLE: 0.3
                            non_ot_rate = (rt / 1.3) - 1  # special day ot rate
                            work_hr_non_ot = {
                                "ot_line_id": ot.id,
                                "date": ot.date,
                                "hours": 8,
                                "rate": non_ot_rate,  # 1.00 already included in holiday pay
                                "rate_type": ot.rate_type,
                                "hourly_rate": vals.hourly_rate * non_ot_rate,
                            }
                            ot_brkdwn.append(work_hr_non_ot)
                            # SAMPLE: HOURLYRATE 67.13 * 1.69, without the night diff
                            work_hr_ot = {
                                "ot_line_id": ot.id,
                                "date": ot.date,
                                "hours": ot.total_ot_hrs - 8,
                                "rate": rt,
                                "rate_type": ot.rate_type,
                                "hourly_rate": vals.hourly_rate,
                            }
                            ot_brkdwn.append(work_hr_ot)

                    else:
                        work_hr_non_ot = {
                            "ot_line_id": ot.id,
                            "date": ot.date,
                            "hours": ot.total_ot_hrs,
                            "rate": rt - 1.00,  # 1.00 already included in holiday pay
                            "rate_type": ot.rate_type,
                            "hourly_rate": hourly_rate,
                        }
                        ot_brkdwn.append(work_hr_non_ot)

                # ON REST DAY ONLY NO HOLIDAY
                elif ot.rate_type in ("1", "9", "17", "25"):

                    if ot.rate_type in ("17", "25"):
                        if ot.total_ot_hrs > 8:
                            non_ot_rate = rt / 1.3  # ordinary ot rate
                            work_hr_non_ot = {
                                "ot_line_id": ot.id,
                                "date": ot.date,
                                "hours": 8,
                                "rate": non_ot_rate,
                                "rate_type": ot.rate_type,
                                "hourly_rate": vals.hourly_rate * non_ot_rate,
                            }
                            ot_brkdwn.append(work_hr_non_ot)

                            work_hr_ot = {
                                "ot_line_id": ot.id,
                                "date": ot.date,
                                "hours": ot.total_ot_hrs - 8,
                                "rate": rt,
                                "rate_type": ot.rate_type,
                                "hourly_rate": hourly_rate,
                            }
                            ot_brkdwn.append(work_hr_ot)
                    else:
                        work_hr_non_ot = {
                            "ot_line_id": ot.id,
                            "date": ot.date,
                            "hours": ot.total_ot_hrs,
                            "rate": rt,
                            "rate_type": ot.rate_type,
                            "hourly_rate": hourly_rate,
                        }
                        ot_brkdwn.append(work_hr_non_ot)

                if has_nd:
                    night_diff = self.compute_ot_night_diff(
                        ot.actual_in, ot.actual_out, ot.date
                    )
                    hrs_for_nd = {
                        "ot_line_id": ot.id,
                        "date": ot.date,
                        "rate_type": ot.rate_type,
                        "rate": nd_rate
                        - 1.00,  # -1 to take just the .1, already computed on the total hours
                        "hours": night_diff,
                        "hourly_rate": hourly_rate * (nd_rate - 1),
                    }
                    ot_brkdwn.append(hrs_for_nd)

            ot_amount_pay = 0
            sunday_ot_amount_pay = 0

            if ot_brkdwn:
                for val in ot_brkdwn:
                    amount = 0
                    self.env["overtime.breakdown.line"].create(val)
                    amount = val["hourly_rate"] * val["hours"]

                    if val["date"].weekday() == 6:
                        ot_amount_pay += amount

                    else:
                        ot_amount_pay += amount

            earning_id = self.env["earnings.type"].search(
                [("name", "=", "Overtime"), ("active", "=", True)], limit=1
            )
            count = self.env["exhr.payslip.earnings"].search_count(
                [("payslip_id", "=", self.id), ("name_id", "=", earning_id.id)]
            )

            if count == 0:
                # nothing found
                # will create earnings line
                self.env["exhr.payslip.earnings"].create(
                    {
                        "payslip_id": self.id,
                        "name_id": earning_id.id,
                        "amount_subtotal": ot_amount_pay,
                        "no_day_hrs": no_day_hrs,
                        "no_day_hrs_disp": (
                            str(round(no_day_hrs, 2)) + " Hours" if no_day_hrs else ""
                        ),
                    }
                )
            else:
                # existing found
                # will update the existing amount
                self.env["exhr.payslip.earnings"].search(
                    [("payslip_id", "=", self.id), ("name_id", "=", earning_id.id)]
                ).write(
                    {
                        "amount_subtotal": ot_amount_pay,
                        "no_day_hrs": no_day_hrs,
                        "no_day_hrs_disp": (
                            str(round(no_day_hrs, 2)) + " Hours" if no_day_hrs else ""
                        ),
                    }
                )

    def prev_day_work_holiday(self, prev_work_day, date_now):
        prev_work_day_date = prev_work_day.date
        is_lwop = False

        if "7" in prev_work_day.schedule_type_ids.ids:  # holiday
            # check next previous date
            if prev_work_day.actual_time_diff == 0:  # no attendance
                is_lwop = True

        if "1" in prev_work_day.schedule_type_ids.ids:  # absent
            is_lwop = True

        elif "2" in prev_work_day.schedule_type_ids.ids:  # leave half day
            leaves = self.env["hr.leave"].search(
                [
                    ("employee_id", "=", self.employee_id.id),
                    ("date_from", "<=", prev_work_day_date),
                    ("date_to", ">=", prev_work_day_date),
                    ("state", "=", "validate"),
                ]
            )
            for l in leaves:
                if l.holiday_status_id.is_unpaid_leave == True:
                    is_lwop = True
        elif "4" in prev_work_day.schedule_type_ids.ids:  # leave
            leaves = self.env["hr.leave"].search(
                [
                    ("employee_id", "=", self.employee_id.id),
                    ("date_from", "<=", prev_work_day_date),
                    ("date_to", ">=", prev_work_day_date),
                    ("state", "=", "validate"),
                ]
            )
            for l in leaves:
                if l.holiday_status_id.is_unpaid_leave == True:
                    is_lwop = True

        elif 1 in prev_work_day.schedule_type_ids.ids:  # absent
            is_lwop = True

        elif 2 in prev_work_day.schedule_type_ids.ids:  # leave half day
            leaves = self.env["hr.leave"].search(
                [
                    ("employee_id", "=", self.employee_id.id),
                    ("date_from", "<=", prev_work_day_date),
                    ("date_to", ">=", prev_work_day_date),
                    ("state", "=", "validate"),
                ]
            )
            for l in leaves:
                if l.holiday_status_id.is_unpaid_leave == True:
                    is_lwop = True
        elif 4 in prev_work_day.schedule_type_ids.ids:  # leave
            leaves = self.env["hr.leave"].search(
                [
                    ("employee_id", "=", self.employee_id.id),
                    ("date_from", "<=", prev_work_day_date),
                    ("date_to", ">=", prev_work_day_date),
                    ("state", "=", "validate"),
                ]
            )
            for l in leaves:
                if l.holiday_status_id.is_unpaid_leave == True:
                    is_lwop = True

        return is_lwop

    def compute_holiday_pay(self, vals):
        """Computes Holiday Pay in Earnings table:
        -If daily wage earner
                - NO Holiday Pay if no attendance
                - With Attendance:
                        - total holiday pay = daily rate + (hours * hourly_rate * percentage rate-1)
        -If NOT daily wage earner
                - If no attendance - NO Holiday Pay
                - If with attendance, Regular holiday - (get percentage of rate in overtime.rate.config-1) * actual_time_diff * hourly rate
                - If with attendance, Special holiday - (get percentage of rate in overtime.rate.config-1) * actual_time_diff * hourly rate
        """
        amount = 0
        no_day_hrs_disp = ""

        att_list = self.env["hr.attendance.sheet"].search(
            [("employee_id", "=", self.employee_id.id), ("payslip_id", "=", self.id)]
        )

        worked_holiday = 0
        holiday_pay = 0
        holiday_pay_deduction = 0

        if vals:  # with contract,will update the payslip base on the found contract
            if vals.daily_wage:
                for a in att_list:
                    worked_rate = 0
                    holiday = self.get_holiday_status(
                        a.date, self.employee_id.exhr_work_location
                    )
                    if holiday.get("count") > 0:  # it is a holiday
                        # print('it is a holiday! : ', a.date)
                        holiday_type = holiday.get("type")

                        # get day before
                        prev_work_day = self.env["hr.attendance.sheet"].search(
                            [
                                ("employee_id", "=", self.employee_id.id),
                                ("date", "<", a.date),
                                (
                                    "rate_type",
                                    "not in",
                                    (1, 3, 5, 7, 9, 10, 11, 13, 15),
                                ),
                            ],
                            order="date desc",
                            limit=1,
                        )
                        prev_work_day_date = prev_work_day.date

                        # check if lwop prev work day
                        is_lwop = self.prev_day_work_holiday(prev_work_day, a.date)
                        # print('prev_work_day_date : ', prev_work_day_date)
                        # print('is_lwop : ', is_lwop)

                        if a.actual_in and a.actual_out:
                            rate_type = dict(
                                self.env["hr.attendance.sheet"].fields_get(
                                    allfields=["rate_type"]
                                )["rate_type"]["selection"]
                            )[a.rate_type]
                            rate_config = self.env["overtime.rate.config"].search(
                                [("name", "=", rate_type)], limit=1
                            )

                            hours = a.actual_time_diff

                            if vals.work_schedule_type == "ww":
                                if hours > 10 and not a.extra:
                                    hours = 10

                            if vals.work_schedule_type == "regular":
                                if hours > 8:
                                    hours = 8

                            worked_rate = (
                                hours * (rate_config.percentage - 1) * vals.hourly_rate
                            )
                            worked_holiday += worked_rate

                            if vals.work_schedule_type == "regular":
                                if holiday_type == "regular":
                                    holiday_pay += round(vals.daily_rate, 2)
                                    # print('here! add holiday pay : ', holiday_pay)
                                else:
                                    holiday_pay += (vals.hourly_rate) * hours

                        else:  # no attendance
                            if not is_lwop:  # if prev worked day is not lwop
                                if (
                                    holiday_type == "regular"
                                ):  # regular holiday, no attendance - should be paid with Holiday Pay (daily rate)
                                    holiday_pay += round(vals.daily_rate, 2)

            else:  # NOT daily wage earner
                for a in att_list:
                    worked_rate = 0
                    holiday = self.get_holiday_status(
                        a.date, self.employee_id.exhr_work_location
                    )
                    if holiday.get("count") > 0:  # it is a holiday
                        holiday_type = holiday.get("type")
                        # print('date : ', a.date)

                        # get day before
                        prev_work_day = self.env["hr.attendance.sheet"].search(
                            [
                                ("employee_id", "=", self.employee_id.id),
                                ("date", "<", a.date),
                                (
                                    "rate_type",
                                    "not in",
                                    (1, 3, 5, 7, 9, 10, 11, 13, 15),
                                ),
                            ],
                            order="date desc",
                            limit=1,
                        )
                        prev_work_day_date = prev_work_day.date
                        # print('prev_work_day_date : ', prev_work_day_date)

                        # check if lwop prev work day
                        is_lwop = self.prev_day_work_holiday(prev_work_day, a.date)
                        # print('is_lwop : ', is_lwop)

                        rate_type = dict(
                            self.env["hr.attendance.sheet"].fields_get(
                                allfields=["rate_type"]
                            )["rate_type"]["selection"]
                        )[a.rate_type]
                        rate_config = self.env["overtime.rate.config"].search(
                            [("name", "=", rate_type)], limit=1
                        )

                        hours = a.actual_time_diff

                        if vals.work_schedule_type == "ww":
                            if hours > 10 and not a.extra:
                                hours = 10

                        if vals.work_schedule_type == "regular":
                            if hours > 8:
                                hours = 8

                        if not is_lwop:  # prev work day is not lwop
                            worked_rate = (
                                hours * (rate_config.percentage - 1) * vals.hourly_rate
                            )
                            worked_holiday += worked_rate

                        if vals.work_schedule_type == "ww":
                            if holiday_type == "regular":
                                holiday_pay += round(vals.daily_rate, 2)
                                if is_lwop:
                                    worked_rate = (
                                        hours
                                        * (rate_config.percentage - 1)
                                        * vals.hourly_rate
                                    )
                                    if worked_rate > 0:
                                        worked_holiday += worked_rate
                                    else:
                                        holiday_pay_deduction += round(
                                            vals.daily_rate, 2
                                        )

                        elif vals.work_schedule_type == "regular":
                            if is_lwop:
                                if holiday_type == "regular":
                                    worked_rate = (
                                        hours
                                        * (rate_config.percentage - 1)
                                        * vals.hourly_rate
                                    )
                                    if worked_rate > 0:
                                        worked_holiday += worked_rate
                                    else:
                                        holiday_pay_deduction += round(
                                            vals.daily_rate, 2
                                        )

                        elif vals.work_schedule_type == "fixed":
                            if holiday_type == "regular":
                                if is_lwop:
                                    worked_rate = (
                                        hours
                                        * (rate_config.percentage - 1)
                                        * vals.hourly_rate
                                    )
                                    if worked_rate > 0:
                                        worked_holiday += worked_rate
                                    else:
                                        holiday_pay_deduction += round(
                                            vals.daily_rate, 2
                                        )

            if vals.work_schedule_type == "regular":
                amount = worked_holiday + holiday_pay
                amount = round(amount, 2)
            elif vals.work_schedule_type == "ww":
                amount = worked_holiday
                amount = round(amount, 2)
            elif vals.work_schedule_type == "fixed":
                amount = worked_holiday
                amount = round(amount, 2)

            # UPDATE EARNINGS LINE - START
            if (
                self.env["earnings.type"].search_count(
                    [("name", "=", "Holiday Pay"), ("active", "=", True)]
                )
                > 0
            ):
                earning_id = self.env["earnings.type"].search(
                    [("name", "=", "Holiday Pay"), ("active", "=", True)], limit=1
                )

                count = self.env["exhr.payslip.earnings"].search_count(
                    [("payslip_id", "=", self.id), ("name_id", "=", earning_id.id)]
                )

                if count == 0:
                    # nothing found
                    # will create earnings line
                    self.env["exhr.payslip.earnings"].create(
                        {
                            "payslip_id": self.id,
                            "name_id": earning_id.id,
                            "amount_subtotal": amount,
                            "no_day_hrs_disp": no_day_hrs_disp,
                        }
                    )
                else:
                    # existing found
                    # will update the existing amount
                    self.env["exhr.payslip.earnings"].search(
                        [("payslip_id", "=", self.id), ("name_id", "=", earning_id.id)]
                    ).write(
                        {"amount_subtotal": amount, "no_day_hrs_disp": no_day_hrs_disp}
                    )

            if (
                self.env["deduction.type"].search_count(
                    [("name", "=", "Holiday w/o Pay"), ("active", "=", True)]
                )
                == 0
            ):
                self.env["deduction.type"].create(
                    {"name": "Holiday w/o Pay", "active": True}
                )

            ded_id = self.env["deduction.type"].search(
                [("name", "=", "Holiday w/o Pay"), ("active", "=", True)], limit=1
            )
            count = self.env["exhr.payslip.deductions"].search_count(
                [("payslip_id", "=", self.id), ("name_id", "=", ded_id.id)]
            )

            if count == 0:
                self.env["exhr.payslip.deductions"].create(
                    {
                        "payslip_id": self.id,
                        "name_id": ded_id.id,
                        "amount_total": holiday_pay_deduction,
                    }
                )
            else:
                self.env["exhr.payslip.deductions"].search(
                    [("payslip_id", "=", self.id), ("name_id", "=", ded_id.id)]
                ).write({"amount_total": holiday_pay_deduction})

        else:
            raise UserError("No Running/To Renew Contract found!")

    def compute_leave_pay(self, vals):
        """Computes Leave Pay in Earnings table:
        - Consider:
                - validated leaves covered in the payroll period (not a rest day based on tagged schedule in contracts, not Unpaid or Undertime)
                - validated leaves before the payroll period , not yet paid in payslip (not a rest day based on tagged schedule in contracts, not Unpaid or Undertime)
        """

        if vals:  # with contract, will update the payslip base on the found contract

            # Delete existing leave_ids // Check if can be reduced to single line code
            old_list = self.env["payslip.leave.line"].search(
                [("payslip_id", "=", self.id)]
            )
            for ln in old_list:
                ln.unlink()

            a = self.pay_period_from
            numdays = (self.pay_period_to - self.pay_period_from).days
            dateList_payroll = (
                []
            )  # list of all dates covered in the payroll period - ex. June6-june20 [06/06/2021, 06/06/2021,... , 06/20/2021]
            for x in range(0, numdays + 1):
                date_payslip = (a + timedelta(days=x)).strftime("%m/%d/%Y")
                dateList_payroll.append(date_payslip)

            # leaves_1 - leaves that are covered in the payroll period (pay_period_from to pay_period_to)
            leaves_1 = (
                self.env["hr.leave"]
                .sudo()
                .search(
                    [
                        ("employee_id", "=", self.employee_id.id),
                        ("request_date_from", "<=", self.pay_period_to),
                        ("request_date_to", ">=", self.pay_period_from),
                        ("state", "=", "validate"),
                    ]
                )
            )
            # leaves_2 - leaves that are NOT covered in the payroll period (request_date_to < pay_period_from), not yet paid in payslip (payslip_status = FALSE)
            leaves_2 = (
                self.env["hr.leave"]
                .sudo()
                .search(
                    [
                        ("employee_id", "=", self.employee_id.id),
                        ("request_date_to", "<", self.pay_period_from),
                        ("state", "=", "validate"),
                        ("payslip_status", "=", False),
                    ]
                )
            )

            leaves = leaves_1 + leaves_2

            count_leave1 = 0
            for l in leaves_1:
                a = l.request_date_from
                numdays = (l.request_date_to - l.request_date_from).days

                for x in range(0, numdays + 1):
                    date_leave = (a + timedelta(days=x)).strftime("%m/%d/%Y")
                    if date_leave in dateList_payroll:

                        date_leave_dow = datetime.strptime(
                            date_leave, "%m/%d/%Y"
                        ).weekday()

                        calendar_line = self.env["resource.calendar.attendance"].search(
                            [
                                "|",
                                "&",
                                ("calendar_id", "=", vals.resource_calendar_id.id),
                                "&",
                                ("dayofweek", "=", str(date_leave_dow)),
                                "&",
                                ("date_from", "<=", date_leave),
                                ("date_to", ">=", date_leave),
                                "&",
                                ("calendar_id", "=", vals.resource_calendar_id.id),
                                "&",
                                ("dayofweek", "=", str(date_leave_dow)),
                                "&",
                                ("date_from", "=", False),
                                ("date_to", "=", False),
                            ],
                            order="date_from asc",
                            limit=1,
                        )

                        if calendar_line:  # check if not a rest day in schedule

                            wsa_line_check = self.env["work.sched.adjustment"].search(
                                [
                                    ("employee_id", "=", self.employee_id.id),
                                    ("date_change", "=", date_leave),
                                    ("status", "=", "validate"),
                                ],
                                order="create_date desc",
                                limit=1,
                            )
                            if not (
                                wsa_line_check.planned_in == 0
                                and wsa_line_check.planned_out == 0
                            ):

                                if l.holiday_status_id.is_unpaid_leave == False:
                                    count_leave1 += 1
                                    if l.request_unit_half:
                                        count_leave1 -= 0.5

                            if not wsa_line_check:
                                if l.holiday_status_id.is_unpaid_leave == False:
                                    count_leave1 += 1
                                    if l.request_unit_half:
                                        count_leave1 -= 0.5
                        else:

                            wsa_line = (
                                self.env["work.sched.adjustment"]
                                .search(
                                    [
                                        ("employee_id", "=", self.employee_id.id),
                                        ("date_change", "=", date_leave),
                                        ("status", "=", "validate"),
                                    ],
                                    order="create_date desc",
                                    limit=1,
                                )
                                .id
                            )
                            if wsa_line:

                                if l.holiday_status_id.is_unpaid_leave == False:

                                    count_leave1 += 1
                                    if l.request_unit_half:
                                        count_leave1 -= 0.5
                    # else:
                    # 	date_leave_dow = datetime.strptime(date_leave,'%m/%d/%Y').weekday()

                    # 	calendar_line = self.env['resource.calendar.attendance'].search(['|','&',('calendar_id','=',vals.resource_calendar_id.id),'&',
                    # 										('dayofweek','=',str(date_leave_dow)),'&',('date_from','<=',date_leave),('date_to','>=',date_leave),
                    # 										'&',('calendar_id','=',vals.resource_calendar_id.id),'&',('dayofweek','=',str(date_leave_dow)),
                    # 										'&',('date_from','=',False),('date_to','=',False)],order='date_from asc',limit=1)

                    # 	if calendar_line: #check if not a rest day in schedule
                    # 		# print('date_leave not in payroll: ', date_leave)
                    # 		if 'Unpaid Leave' not in l.holiday_status_id.name and 'Maternity Leave' not in l.holiday_status_id.name and 'Undertime' not in l.holiday_status_id.name:
                    # 			count_leave1 += 1
                    # 			if l.request_unit_half:
                    # 				count_leave1 -= 0.5
                    # else:
                    # 	wsa_line = self.env['work.sched.adjustment'].search([('employee_id','=',self.employee_id.id),('date_change','=',date_leave),('status','=','validate')],order='date_change asc',limit=1)
                    # 	if wsa_line:
                    # 		if 'Unpaid Leave' not in l.holiday_status_id.name and 'Maternity Leave' not in l.holiday_status_id.name and 'Undertime' not in l.holiday_status_id.name:
                    # 			count_leave1 += 1
                    # 			if l.request_unit_half:
                    # 				count_leave1 -= 0.5
            count_leave2 = 0
            for l in leaves_2:
                a = l.request_date_from
                numdays = (l.request_date_to - l.request_date_from).days

                for x in range(0, numdays + 1):
                    date_leave = (a + timedelta(days=x)).strftime("%m/%d/%Y")

                    date_leave_dow = datetime.strptime(date_leave, "%m/%d/%Y").weekday()
                    calendar_line = self.env["resource.calendar.attendance"].search(
                        [
                            "|",
                            "&",
                            ("calendar_id", "=", vals.resource_calendar_id.id),
                            "&",
                            ("dayofweek", "=", str(date_leave_dow)),
                            "&",
                            ("date_from", "<=", date_leave),
                            ("date_to", ">=", date_leave),
                            "&",
                            ("calendar_id", "=", vals.resource_calendar_id.id),
                            "&",
                            ("dayofweek", "=", str(date_leave_dow)),
                            "&",
                            ("date_from", "=", False),
                            ("date_to", "=", False),
                        ],
                        order="date_from asc",
                        limit=1,
                    )

                    if calendar_line:  # check if not a rest day in schedule
                        # print('date_leave2 : ', date_leave)
                        wsa_line_check = self.env["work.sched.adjustment"].search(
                            [
                                ("employee_id", "=", self.employee_id.id),
                                ("date_change", "=", date_leave),
                                ("status", "=", "validate"),
                            ],
                            order="create_date desc",
                            limit=1,
                        )
                        # ,('planned_in','=',0),('planned_out','=',0)

                        if not (
                            wsa_line_check.planned_in == 0
                            and wsa_line_check.planned_out == 0
                        ):
                            if l.holiday_status_id.is_unpaid_leave == False:
                                count_leave2 += 1
                                if l.request_unit_half:
                                    count_leave2 -= 0.5
                        if not wsa_line_check:
                            if l.holiday_status_id.is_unpaid_leave == False:
                                count_leave2 += 1
                                if l.request_unit_half:
                                    count_leave2 -= 0.5
                    else:
                        wsa_line = self.env["work.sched.adjustment"].search(
                            [
                                ("employee_id", "=", self.employee_id.id),
                                ("date_change", "=", date_leave),
                                ("status", "=", "validate"),
                            ],
                            order="create_date desc",
                            limit=1,
                        )
                        if wsa_line:
                            if l.holiday_status_id.is_unpaid_leave == False:
                                count_leave2 += 1
                                if l.request_unit_half:
                                    count_leave2 -= 0.5

            days = count_leave1 + count_leave2
            # print('count_leave1 : ', count_leave1)
            # print('count_leave2 : ', count_leave2)

            # write in leave_ids
            leaves_line_obj = self.env["payslip.leave.line"]
            for l in leaves:
                vals_time_off = {
                    "payslip_id": self.id,
                    "leaves_id": l.id,
                    "holiday_status_id": l.holiday_status_id.id,
                    "days": count_leave1 + count_leave2,
                }
                leaves_line_obj.create(vals_time_off)

            if (
                self.env["earnings.type"].search_count(
                    [("name", "=", "Leave Pay"), ("active", "=", True)]
                )
                > 0
            ):
                amount = days * vals.daily_rate
                no_day_hrs_disp = str(round(days, 2)) + " Days" if days else ""

                earning_id = self.env["earnings.type"].search(
                    [("name", "=", "Leave Pay"), ("active", "=", True)], limit=1
                )

                count = self.env["exhr.payslip.earnings"].search_count(
                    [("payslip_id", "=", self.id), ("name_id", "=", earning_id.id)]
                )

                if count == 0:
                    # nothing found
                    # will create earnings line
                    self.env["exhr.payslip.earnings"].create(
                        {
                            "payslip_id": self.id,
                            "name_id": earning_id.id,
                            "amount_subtotal": amount,
                            "no_day_hrs_disp": no_day_hrs_disp,
                        }
                    )
                else:
                    # existing found
                    # will update the existing amount
                    self.env["exhr.payslip.earnings"].search(
                        [("payslip_id", "=", self.id), ("name_id", "=", earning_id.id)]
                    ).write(
                        {"amount_subtotal": amount, "no_day_hrs_disp": no_day_hrs_disp}
                    )

            else:
                raise UserError("No Holiday Pay found on earnings configuration.")

        else:
            raise UserError("No Running/To Renew Contract found!")

    def compute_leave_wo_pay(self, vals):
        """Computes Leave w/o Pay in Deduction table:
        - Consider:
                - Working Schedule - Regular and Fixed
                - scenarios where Leave w/o pay = 0:
                        - daily wage earner
                        - 48H WW working schedule
                        - N/A working schedule

        """
        if vals:
            days_leave_wo_pay = self.total_working_days - self.no_days_present
            att_list = self.env["hr.attendance.sheet"].search(
                [
                    ("employee_id", "=", self.employee_id.id),
                    ("payslip_id", "=", self.id),
                ]
            )
            reg_count = 0

            for rec in att_list:
                if att_list[0].work_schedule_type == "regular":
                    # if '1' in rec.schedule_type_ids.ids: #absent
                    # 	reg_count += 1
                    # 	print('date : ', rec.date)
                    if (
                        4 in rec.schedule_type_ids.ids
                        and rec.actual_in
                        and rec.actual_out
                    ):  # on leave, with attendance
                        added = 1
                        leaves = (
                            self.env["hr.leave"]
                            .sudo()
                            .search(
                                [
                                    ("employee_id", "=", self.employee_id.id),
                                    ("request_date_from", "<=", rec.date),
                                    ("request_date_to", ">=", rec.date),
                                    ("state", "=", "validate"),
                                ]
                            )
                        )
                        for leave in leaves:
                            if leave.holiday_status_id.name == "Undertime":
                                added = 0
                        days_leave_wo_pay += added
                    if (
                        2 in rec.schedule_type_ids.ids
                        and rec.actual_in
                        and rec.actual_out
                    ):  # on half-day leave, with attendance
                        days_leave_wo_pay += 0.5
                    # if 7 in rec.schedule_type_ids.ids and rec.actual_in and rec.actual_out: #holiday working day, with attendance
                    # 	days_leave_wo_pay += 1
                    if rec.rate_type in ["1"] and rec.actual_in and rec.actual_out:
                        days_leave_wo_pay += 1
                    # print('lwop : ', days_leave_wo_pay)

                if att_list[0].work_schedule_type == "fixed":
                    # print('schedule_id: ',rec.schedule_type_ids.ids)
                    if (
                        4 in rec.schedule_type_ids.ids
                        and rec.actual_in
                        and rec.actual_out
                    ):  # on leave, with attendance
                        days_leave_wo_pay += 1
                    if (
                        2 in rec.schedule_type_ids.ids
                        and rec.actual_in
                        and rec.actual_out
                    ):  # on half-day leave, with attendance
                        days_leave_wo_pay += 0.5
                        # print('half day')
                    if (
                        7 in rec.schedule_type_ids.ids
                        and rec.actual_in
                        and rec.actual_out
                    ):  # holiday working day, with attendance
                        days_leave_wo_pay += 1
                    if rec.rate_type in ["1"] and rec.actual_in and rec.actual_out:
                        days_leave_wo_pay += 1

                if att_list[0].work_schedule_type == "na":
                    days_leave_wo_pay = 0

                if att_list[0].work_schedule_type == "ww":
                    days_leave_wo_pay = 0

            # if att_list[0].work_schedule_type == 'regular' and not vals.daily_wage:
            # 	days_leave_wo_pay = reg_count
            # 	print('here')

            if vals.daily_wage:
                days_leave_wo_pay = 0

            if days_leave_wo_pay < 0:
                days_leave_wo_pay = 0

            # print('reg_count : ', reg_count)

            amount = days_leave_wo_pay * vals.daily_rate
            no_day_hrs_disp = (
                str(days_leave_wo_pay) + " Days" if days_leave_wo_pay else ""
            )

            # with contract
            # will update the payslip base on the found contract
            if (
                self.env["deduction.type"].search_count(
                    [("name", "=", "Leave w/o pay"), ("active", "=", True)]
                )
                > 0
            ):
                deduction_id = self.env["deduction.type"].search(
                    [("name", "=", "Leave w/o pay"), ("active", "=", True)], limit=1
                )

                count = self.env["exhr.payslip.deductions"].search_count(
                    [("payslip_id", "=", self.id), ("name_id", "=", deduction_id.id)]
                )

                if count == 0:
                    # nothing found
                    # will create deductions line
                    self.env["exhr.payslip.deductions"].create(
                        {
                            "payslip_id": self.id,
                            "name_id": deduction_id.id,
                            "amount_total": amount,
                            "no_day_hrs_disp": no_day_hrs_disp,
                        }
                    )
                else:
                    # existing found
                    # will update the existing amount
                    self.env["exhr.payslip.deductions"].search(
                        [
                            ("payslip_id", "=", self.id),
                            ("name_id", "=", deduction_id.id),
                        ]
                    ).write(
                        {"amount_total": amount, "no_day_hrs_disp": no_day_hrs_disp}
                    )

            else:
                raise UserError("No Leave w/o pay found on deductions configuration.")

        else:
            raise UserError("No Running/To Renew Contract found!")

    def compute_tardiness(self, vals):
        """Computes Tardiness Deduction in DEDUCTION table:
        - Consider:
                - Working Schedule - Regular ONLY
        """
        if vals:  # with contract,will update the payslip based on the found contract
            if vals.work_schedule_type == "regular":
                att_list = self.env["hr.attendance.sheet"].search(
                    [
                        ("employee_id", "=", self.employee_id.id),
                        ("payslip_id", "=", self.id),
                    ]
                )

                mins = sum([a.mins_for_late for a in att_list])

                if (
                    self.env["deduction.type"].search_count(
                        [("name", "=", "Tardiness"), ("active", "=", True)]
                    )
                    > 0
                ):
                    deduction_id = self.env["deduction.type"].search(
                        [("name", "=", "Tardiness"), ("active", "=", True)], limit=1
                    )
                    count = self.env["exhr.payslip.deductions"].search_count(
                        [
                            ("payslip_id", "=", self.id),
                            ("name_id", "=", deduction_id.id),
                        ]
                    )

                    amount = round(mins / 60, 2) * vals.hourly_rate
                    no_day_hrs_disp = str(round(mins / 60, 2)) + " Hrs" if mins else ""

                    if count == 0:
                        # nothing found
                        # will create deductions line
                        self.env["exhr.payslip.deductions"].create(
                            {
                                "payslip_id": self.id,
                                "name_id": deduction_id.id,
                                "amount_total": amount,
                                "no_day_hrs_disp": no_day_hrs_disp,
                            }
                        )
                    else:
                        # existing found
                        # will update the existing amount
                        self.env["exhr.payslip.deductions"].search(
                            [
                                ("payslip_id", "=", self.id),
                                ("name_id", "=", deduction_id.id),
                            ]
                        ).write(
                            {"amount_total": amount, "no_day_hrs_disp": no_day_hrs_disp}
                        )

                else:
                    raise UserError("No Tardiness found on deduction configuration.")

        else:
            raise UserError("No Running/To Renew Contract found!")

    def compute_undertime(self, vals):
        """Computes Undertime Deduction in Deduction table:
        - Consider:
                - Working Schedule - Regular and 48HWW:
                        - REGULAR Working Schedule - sum of undertime mins from attendance sheet (mins_for_undertime)
                        - 48H WW Working Schedule - (total working days*8) - actual worked hours
                                - actual worked hours -limit 10 hours per day, unless ticked as 'extra'
        """
        if vals:  # with contract,will update the payslip base on the found contract
            att_list = self.env["hr.attendance.sheet"].search(
                [
                    ("employee_id", "=", self.employee_id.id),
                    ("payslip_id", "=", self.id),
                ]
            )

            amount = 0
            hours = 0

            if vals.work_schedule_type == "regular":
                if vals.daily_wage:
                    mins = sum(
                        [
                            (
                                a.mins_for_undertime
                                if "7" not in a.schedule_type_ids.ids
                                else 0
                            )
                            for a in att_list
                        ]
                    )
                else:
                    mins = sum([a.mins_for_undertime for a in att_list])

                amount = round(mins / 60, 2) * vals.hourly_rate
                hours = mins / 60

            if vals.work_schedule_type == "ww":
                total_hours = 0

                for a in att_list:
                    if a.actual_time_diff > 10 and not a.extra:
                        total_hours += 10
                    else:
                        total_hours += a.actual_time_diff

                diff = (self.total_working_days * 8) - total_hours

                if diff > 0:
                    amount = diff * vals.hourly_rate
                    hours = diff
                if diff <= 0:
                    amount = 0
                    hours = 0

            if (
                self.env["deduction.type"].search_count(
                    [("name", "=", "Undertime"), ("active", "=", True)]
                )
                > 0
            ):
                deduction_id = self.env["deduction.type"].search(
                    [("name", "=", "Undertime"), ("active", "=", True)], limit=1
                )

                count = self.env["exhr.payslip.deductions"].search_count(
                    [("payslip_id", "=", self.id), ("name_id", "=", deduction_id.id)]
                )
                no_day_hrs_disp = str(round(hours, 2)) + " Hrs" if hours else ""

                if count == 0:
                    # nothing found
                    # will create deductions line
                    self.env["exhr.payslip.deductions"].create(
                        {
                            "payslip_id": self.id,
                            "name_id": deduction_id.id,
                            "amount_total": amount,
                            "no_day_hrs_disp": no_day_hrs_disp,
                        }
                    )
                else:
                    # existing found
                    # will update the existing amount
                    self.env["exhr.payslip.deductions"].search(
                        [
                            ("payslip_id", "=", self.id),
                            ("name_id", "=", deduction_id.id),
                        ]
                    ).write(
                        {"amount_total": amount, "no_day_hrs_disp": no_day_hrs_disp}
                    )

            else:
                raise UserError("No Undertime found on deduction configuration.")

        else:
            raise UserError("No Running/To Renew Contract found!")

    def compute_allowance(self, vals):
        """Computes Allowances from Contracts in OTHER EARNINGS/CHARGES table"""
        nontax_obj = self.env["exhr.payslip.nontaxable"]
        if vals:
            deduction_id = self.env["nontaxable.type"].search(
                [("name", "=", "Allowance"), ("active", "=", True)]
            )

            total_hrs = (
                self.hrs_for_prorate
            )  # total hours for the payroll period - De Minimis, Responsibility Allowance, Disturbance Allowance
            total_days_present = self.no_days_present  # total days present - COLA
            prev_total_hrs = 0  # total hours for the previous payroll period (same month cutoff) - De Minimis, Responsibility Allowance, Disturbance Allowance
            prev_total_days_present = 0  # total days for the previous payroll period (same month cutoff) - COLA

            prev_payslip = self.env["exhr.payslip"].search(
                [
                    ("employee_id", "=", self.employee_id.id),
                    ("company_id", "=", self.company_id.id),
                    ("id", "!=", self.id),
                ]
            )

            for payslip in prev_payslip:
                if (
                    payslip.cutoff_date.year == self.cutoff_date.year
                    and payslip.cutoff_date.month == self.cutoff_date.month
                    and payslip.payroll_id.for_13th_mo == False
                    and payslip.cutoff_date.day in (12, 13, 14, 15, 16, 17)
                ):  # FOR CHECKING - maybe can be improved (12,13,14,15,16,17)
                    prev_total_hrs += payslip.hrs_for_prorate
                    prev_total_days_present += payslip.no_days_present

            if (
                self.env["nontaxable.type"].search_count(
                    [("name", "=", "Allowance"), ("active", "=", True)]
                )
                > 0
            ):
                deduction_id = self.env["nontaxable.type"].search(
                    [("name", "=", "Allowance"), ("active", "=", True)]
                )

                allowance_list = self.env["cash.allowance"].search(
                    [("contract_id", "=", vals.id)]
                )  # allowances in employee's contract

                allowance = []  # included allowance for the payroll period
                for a in allowance_list:
                    if a.allowance_1st_app_date == "every_cutoff":
                        allowance.append(a)
                    else:
                        if int(a.allowance_1st_app_date) == self.cutoff_date.day:
                            allowance.append(a)

                        if (
                            int(a.allowance_1st_app_date) != self.cutoff_date.day
                        ):  # applicable for all months (inc. february)
                            if int(a.allowance_1st_app_date) == 30:
                                if self.cutoff_date.day in [25, 26, 27, 28, 29, 30, 31]:
                                    allowance.append(a)
                            if int(a.allowance_1st_app_date) == 15:
                                if self.cutoff_date.day in [11, 12, 13, 14, 15]:
                                    allowance.append(a)

                    if a.allowance_2nd_app_date == "every_cutoff":  # Not Used in AVSC
                        allowance.append(a)

                    else:  # Not Used in AVSC
                        if int(a.allowance_2nd_app_date) == self.cutoff_date.day:
                            allowance.append(a)

                        if (
                            int(a.allowance_2nd_app_date) != self.cutoff_date.day
                        ):  # applicable for all months (inc. february)
                            if int(a.allowance_2nd_app_date) == 30:
                                if self.cutoff_date.day in [25, 26, 27, 28, 29, 30, 31]:
                                    allowance.append(a)
                            if int(a.allowance_2nd_app_date) == 15:
                                if self.cutoff_date.day in [11, 12, 13, 14, 15]:
                                    allowance.append(a)

                for line in allowance:
                    if line.name in [
                        "De Minimis",
                        "Responsibility Allowance",
                        "Disturbance Allowance",
                    ]:
                        try:  # if 30th in allowance
                            if int(line.allowance_1st_app_date) == 30:
                                total_hrs_for_prorate = total_hrs + prev_total_hrs

                        except:  # if every cutoff in allowance
                            total_hrs_for_prorate = total_hrs

                        amount = (
                            (line.amount * vals.eemr_months / vals.eemr_days)
                            / vals.eemr_hours
                        ) * total_hrs_for_prorate  # prorate computation

                        if vals.work_schedule_type == "na":
                            if line.allowance_1st_app_date == "every_cutoff":
                                amount = line.amount / 2
                            else:
                                amount = line.amount

                    elif line.name in ["COLA"]:
                        try:  # if 30th in allowance
                            if int(line.allowance_1st_app_date) == 30:
                                total_days_present_for_cola = (
                                    total_days_present + prev_total_days_present
                                )
                        except:  # if every cutoff in allowance
                            total_days_present_for_cola = total_days_present

                        amount = line.amount * total_days_present_for_cola

                    else:  # NOT De Minimis, Responsibility Allowance, Disturbance Allowance,COLA
                        if line.allowance_1st_app_date == "every_cutoff":
                            amount = line.amount / 2
                        else:
                            amount = line.amount

                    if vals.work_schedule_type == "fixed":
                        if line.allowance_1st_app_date == "every_cutoff":
                            amount = line.amount / 2
                        else:
                            amount = line.amount

                    amount = round(amount, 3)
                    p_last = str(amount)[-1]
                    p_last = int(p_last)

                    if p_last >= 5:
                        k = 10 - p_last
                        amount = amount + (k * 0.001)
                        amount = round(amount, 2)
                    else:
                        amount = round(amount, 2)

                    new_nontax_obj = nontax_obj.create(
                        {
                            "pay_type": "earnings",
                            "payslip_id": self.id,
                            "name_id": deduction_id.id,
                            "ref": line.name,
                            "amount_total": amount,
                            "taxable": line.taxable,
                            "gl_account_id": line.contract_id.employee_id.accounting_tag_id.default_others_account_id.id,
                        }
                    )
                    new_nontax_obj.onchange_amount_total()

    def compute_loans(self, vals):
        """Computes Loan Deductions from Contracts in OTHER EARNINGS/CHARGES table:"""
        nontax_obj = self.env["exhr.payslip.nontaxable"]
        if (
            self.env["nontaxable.type"].search_count(
                [("name", "=", "Loan Deductions"), ("active", "=", True)]
            )
            > 0
        ):
            deduction_id = self.env["nontaxable.type"].search(
                [("name", "=", "Loan Deductions"), ("active", "=", True)]
            )

            loans_list = self.env["loan.monitoring"].search(
                [("contract_id", "=", vals.id)]
            )

            for line in loans_list:
                if line.balance > 0:
                    if line.monthly_deduction_date == "every_cutoff":
                        if vals.payroll_type_id.name == "Monthly":
                            amt = line.monthly_amortization
                        if vals.payroll_type_id.name == "Semi-Monthly":
                            amt = line.monthly_amortization / 2

                    if line.monthly_deduction_date != "every_cutoff":
                        amt = line.monthly_amortization

                    if line.balance < amt:
                        amt = line.balance
                    # will create deductions line
                    # if (line.monthly_deduction_date == 'every_cutoff') or (int(line.monthly_deduction_date) >= date_from.day and int(line.monthly_deduction_date) <= date_to.day):
                    if (
                        (line.monthly_deduction_date == "every_cutoff")
                        or (int(line.monthly_deduction_date) == self.cutoff_date)
                        or (
                            int(line.monthly_deduction_date) != self.cutoff_date
                            and int(line.monthly_deduction_date) == 30
                            and self.cutoff_date.day in [25, 26, 27, 28, 29, 30, 31]
                        )
                        or (
                            int(line.monthly_deduction_date) != self.cutoff_date
                            and int(line.monthly_deduction_date) == 15
                            and self.cutoff_date.day in [11, 12, 13, 14, 15]
                        )
                    ):
                        if self.cutoff_date >= line.period_from:
                            new_nontax_obj = nontax_obj.create(
                                {
                                    "pay_type": "deductions",
                                    "payslip_id": self.id,
                                    "name_id": deduction_id.id,
                                    "new_loan_name": line.loan_name,
                                    "ref": line.loan_type_id.name,
                                    "amount_total": amt,
                                    "loan_id": line.id,
                                    "gl_account_id": line.gl_account.id,
                                }
                            )
                            new_nontax_obj.onchange_amount_total()

                            if new_nontax_obj:
                                new_nontax_obj.onchange_amount_total()

    def compute_sss(self, vals):
        """Computes SSS Contribution based on contract salary (as per AVSC Policy) in DEDUCTIONS table:"""
        valid = 1

        if vals:
            # with contract
            # will update the payslip base on the found contract
            if (
                self.env["deduction.type"].search_count(
                    [("name", "=", "SSS Contribution"), ("active", "=", True)]
                )
                > 0
            ):
                deduction_id = self.env["deduction.type"].search(
                    [("name", "=", "SSS Contribution"), ("active", "=", True)]
                )

                amount = vals.wage

                sss_config = self.env["sss.contribution.config"].search(
                    [("range_from", "<=", amount), ("range_to", ">=", amount)], limit=1
                )

                if sss_config:
                    if vals.sss_1st_co_date and vals.sss_2nd_co_date:
                        er_ss_contri = sss_config.er_ss_contri / 2  # ER (Regular SS)
                        ee_ss_contri = sss_config.ee_ss_contri / 2  # EE (Regular SS)
                        total_ss_contri = (
                            sss_config.total_ss_contri / 2
                        )  # Total (Regular SS)

                        er_ec_contri = (
                            sss_config.er_ec_contri / 2
                        )  # ER (Employee's Compensation)
                        ee_ec_contri = (
                            sss_config.ee_ec_contri / 2
                        )  # EE (Employee's Compensation)
                        total_ec_contri = (
                            sss_config.total_ec_contri / 2
                        )  # Total (Employee's Compensation)

                        er_provident_fund = (
                            sss_config.er_provident_fund / 2
                        )  # ER (Mandatory Provident Fund)
                        ee_provident_fund = (
                            sss_config.ee_provident_fund / 2
                        )  # EE (Mandatory Provident Fund)
                        total_provident_fund = (
                            sss_config.total_provident_fund / 2
                        )  # Total (Mandatory Provident Fund)

                        total_er_ss = sss_config.total_er_ss / 2  # ER Total
                        total_ee_ss = sss_config.total_ee_ss / 2  # EE Total
                        total_ss = sss_config.total_ss / 2  # Total

                    elif vals.sss_1st_co_date and not vals.sss_2nd_co_date:
                        co_date = datetime.strptime(
                            "%s-%s-%s"
                            % (
                                datetime.today().year,
                                datetime.today().month,
                                vals.sss_1st_co_date,
                            ),
                            "%Y-%m-%d",
                        ).date()

                        if (
                            datetime.strptime(self.pay_period_from, "%Y-%m-%d").date()
                            <= co_date
                            and datetime.strptime(self.pay_period_to, "%Y-%m-%d").date()
                            >= co_date
                        ):
                            er_ss_contri = sss_config.er_ss_contri  # ER (Regular SS)
                            ee_ss_contri = sss_config.ee_ss_contri  # EE (Regular SS)
                            total_ss_contri = (
                                sss_config.total_ss_contri
                            )  # Total (Regular SS)

                            er_ec_contri = (
                                sss_config.er_ec_contri
                            )  # ER (Employee's Compensation)
                            ee_ec_contri = (
                                sss_config.ee_ec_contri
                            )  # EE (Employee's Compensation)
                            total_ec_contri = (
                                sss_config.total_ec_contri
                            )  # Total (Employee's Compensation)

                            er_provident_fund = (
                                sss_config.er_provident_fund
                            )  # ER (Mandatory Provident Fund)
                            ee_provident_fund = (
                                sss_config.ee_provident_fund
                            )  # EE (Mandatory Provident Fund)
                            total_provident_fund = (
                                sss_config.total_provident_fund
                            )  # Total (Mandatory Provident Fund)

                            total_er_ss = sss_config.total_er_ss  # ER Total
                            total_ee_ss = sss_config.total_ee_ss  # EE Total
                            total_ss = sss_config.total_ss  # Total
                        else:
                            valid = 0

                    else:
                        raise UserError("Invalid config of SSS cut-off")

                    # print('sss1 : ',total_ee_ss)
                    total_ee_ss = round(total_ee_ss, 3)
                    p_last = str(total_ee_ss)[-1]
                    p_last = int(p_last)

                    if p_last >= 5:
                        k = 10 - p_last
                        total_ee_ss = total_ee_ss + (k * 0.001)
                        total_ee_ss = round(total_ee_ss, 2)
                    else:
                        total_ee_ss = round(total_ee_ss, 2)

                    total_er_ss = round(total_er_ss, 3)
                    e_last = str(total_er_ss)[-1]
                    e_last = int(e_last)

                    if e_last >= 5:
                        j = 10 - e_last
                        total_er_ss = total_er_ss + (k * 0.001)
                        total_er_ss = round(total_er_ss, 2)
                    else:
                        total_er_ss = round(total_er_ss, 2)

                    # print('sss2 : ',total_ee_ss)

                    if valid == 1:
                        count = self.env["exhr.payslip.deductions"].search_count(
                            [
                                ("payslip_id", "=", self.id),
                                ("name_id", "=", deduction_id.id),
                            ]
                        )

                        if count == 0:
                            # nothing found
                            # will create deductions line
                            self.env["exhr.payslip.deductions"].create(
                                {
                                    "payslip_id": self.id,
                                    "name_id": deduction_id.id,
                                    "amount_total": total_ee_ss,
                                    "personal_contri": total_ee_ss,
                                    "employer_contri": total_er_ss,
                                }
                            )

                        else:
                            # existing found
                            # will update the existing amount
                            self.env["exhr.payslip.deductions"].search(
                                [
                                    ("payslip_id", "=", self.id),
                                    ("name_id", "=", deduction_id.id),
                                ]
                            ).write(
                                {
                                    "amount_total": total_ee_ss,
                                    "personal_contri": total_ee_ss,
                                    "employer_contri": total_er_ss,
                                }
                            )

                        sss_lines = self.env["sss.contribution.line"].create(
                            {
                                "payslip_id": self.id,
                                "date": self.cutoff_date,
                                "er_regular_amount": er_ss_contri,
                                "ee_regular_amount": ee_ss_contri,
                                "er_ec_amount": er_ec_contri,
                                "ee_ec_amount": ee_ec_contri,
                                "er_mpf_amount": er_provident_fund,
                                "ee_mpf_amount": ee_provident_fund,
                            }
                        )

                else:
                    raise UserError("Wage not in SSS Contri. range")

    def compute_phic(self, vals):
        """Computes PHIC Contribution based on contract salary (as per AVSC Policy) in DEDUCTIONS table:
        - checking for PHIC config table is based on monthly salary
        - computation of PHIC contri (3%) is based on Base Salary
        """
        valid = 1
        if vals:

            if (
                self.env["deduction.type"].search_count(
                    [("name", "=", "PHIC Contribution"), ("active", "=", True)]
                )
                > 0
            ):
                deduction_id = self.env["deduction.type"].search(
                    [("name", "=", "PHIC Contribution"), ("active", "=", True)]
                )

                amount = (
                    self.env["exhr.payslip.earnings"]
                    .search(
                        [
                            ("name_id.name", "=", "Base Salary"),
                            ("payslip_id", "=", self.id),
                        ],
                        limit=1,
                    )
                    .amount_subtotal
                )

                phic_config = self.env["phic.contribution.config"].search(
                    [("range_from", "<=", vals.wage), ("range_to", ">=", vals.wage)]
                )

                if phic_config:
                    if vals.phic_1st_co_date and vals.phic_2nd_co_date:
                        if phic_config.percent_decimal != 0:
                            personal_contri = (
                                amount * phic_config.percent_decimal / 100
                            ) / 2
                            employer_contri = (
                                amount * phic_config.percent_decimal / 100
                            ) / 2
                        else:
                            personal_contri = phic_config.personal_contri / 2
                            employer_contri = phic_config.employer_contri / 2

                    elif vals.phic_1st_co_date and not vals.phic_2nd_co_date:
                        co_date = datetime.strptime(
                            "%s-%s-%s"
                            % (
                                datetime.today().year,
                                datetime.today().month,
                                vals.phic_1st_co_date,
                            ),
                            "%Y-%m-%d",
                        ).date()

                        if (
                            datetime.strptime(self.pay_period_from, "%Y-%m-%d").date()
                            >= co_date
                            and datetime.strptime(self.pay_period_to, "%Y-%m-%d").date()
                            <= co_date
                        ):
                            if phic_config.percent_decimal != 0:
                                personal_contri = (
                                    amount * phic_config.percent_decimal / 100
                                )
                                employer_contri = (
                                    amount * phic_config.percent_decimal / 100
                                )
                            else:
                                personal_contri = phic_config.personal_contri
                                employer_contri = phic_config.employer_contri
                        else:
                            valid = 0

                    else:
                        raise UserError("Invalid config of PHIC cut-off")

                    # print('phic1 : ',personal_contri)
                    personal_contri = round(personal_contri, 3)
                    p_last = str(personal_contri)[-1]
                    p_last = int(p_last)

                    if p_last >= 5:
                        k = 10 - p_last
                        personal_contri = personal_contri + (k * 0.001)
                        personal_contri = round(personal_contri, 2)
                    else:
                        personal_contri = round(personal_contri, 2)

                    employer_contri = round(employer_contri, 3)
                    e_last = str(employer_contri)[-1]
                    e_last = int(e_last)

                    if e_last >= 5:
                        j = 10 - e_last
                        employer_contri = employer_contri + (k * 0.001)
                        employer_contri = round(employer_contri, 2)
                    else:
                        employer_contri = round(employer_contri, 2)

                    # print('phic2 : ',personal_contri)

                    if personal_contri < 125:
                        personal_contri = 125
                    if employer_contri < 125:
                        employer_contri = 125

                    if valid == 1:
                        count = self.env["exhr.payslip.deductions"].search_count(
                            [
                                ("payslip_id", "=", self.id),
                                ("name_id", "=", deduction_id.id),
                            ]
                        )
                        if count == 0:
                            # nothing found
                            # will create deductions line
                            self.env["exhr.payslip.deductions"].create(
                                {
                                    "payslip_id": self.id,
                                    "name_id": deduction_id.id,
                                    "amount_total": personal_contri,
                                    "personal_contri": personal_contri,
                                    "employer_contri": employer_contri,
                                }
                            )
                        else:
                            # existing found
                            # will update the existing amount
                            self.env["exhr.payslip.deductions"].search(
                                [
                                    ("payslip_id", "=", self.id),
                                    ("name_id", "=", deduction_id.id),
                                ]
                            ).write(
                                {
                                    "amount_total": personal_contri,
                                    "personal_contri": personal_contri,
                                    "employer_contri": employer_contri,
                                }
                            )

                        phic_lines = self.env["phic.contribution.line"].create(
                            {
                                "payslip_id": self.id,
                                "date": self.pay_period_to,
                                "ee_amount": personal_contri,
                                "er_amount": employer_contri,
                            }
                        )

                else:
                    raise UserError("Wage not in PHIC Contri. range")

    def compute_hdmf(self, vals):
        """Computes HDMF Contribution based on contract salary (as per AVSC Policy) in DEDUCTIONS table:
        - checking for HDMF config table is based on contract monthly salary
        - computation of PHIC contri (3%) is based on Base Salary
        """
        valid = 0
        if vals:

            if (
                self.env["deduction.type"].search_count(
                    [("name", "=", "HDMF Contribution"), ("active", "=", True)]
                )
                > 0
            ):
                deduction_id = self.env["deduction.type"].search(
                    [("name", "=", "HDMF Contribution"), ("active", "=", True)]
                )

                amount = (
                    self.env["exhr.payslip.earnings"]
                    .search(
                        [
                            ("name_id.name", "=", "Base Salary"),
                            ("payslip_id", "=", self.id),
                        ],
                        limit=1,
                    )
                    .amount_subtotal
                )

                hdmf_config = self.env["hdmf.contribution.config"].search(
                    [("range_from", "<=", vals.wage), ("range_to", ">=", vals.wage)],
                    limit=1,
                )

                if hdmf_config:
                    if (
                        hdmf_config.max_compensation != 0
                        and amount > hdmf_config.max_compensation
                    ):
                        amount = hdmf_config.max_compensation

                    personal_contri = amount * hdmf_config.personal_contri
                    employer_contri = amount * hdmf_config.employer_contri

                    if vals.hdmf_contri_amount > 0:
                        personal_contri = vals.hdmf_contri_amount
                        valid = 1

                    if vals.hdmf_1st_co_date and vals.hdmf_2nd_co_date:
                        valid = 1

                    if vals.hdmf_1st_co_date and not vals.hdmf_2nd_co_date:
                        co_date = datetime.strptime(
                            "%s-%s-%s"
                            % (
                                datetime.today().year,
                                datetime.today().month,
                                vals.hdmf_1st_co_date,
                            ),
                            "%Y-%m-%d",
                        ).date()
                        if (
                            datetime.strptime(self.pay_period_from, "%Y-%m-%d").date()
                            <= co_date
                            and datetime.strptime(self.pay_period_to, "%Y-%m-%d").date()
                            >= co_date
                        ):
                            personal_contri = personal_contri
                            employer_contri = employer_contri
                            valid = 1
                        else:
                            valid = 0

                    # print('hdmf1 : ',personal_contri)

                    personal_contri = round(personal_contri, 3)
                    p_last = str(personal_contri)[-1]
                    p_last = int(p_last)

                    if p_last >= 5:
                        k = 10 - p_last
                        personal_contri = personal_contri + (k * 0.001)
                        personal_contri = round(personal_contri, 2)
                    else:
                        personal_contri = round(personal_contri, 2)

                    # print('hdmf2 : ',personal_contri)
                    personal_contri = 100 if personal_contri < 100 else personal_contri
                    if vals.hdmf_contri_amount > 0:
                        personal_contri = vals.hdmf_contri_amount
                    else:
                        personal_contri = 100

                    # perform line creation
                    if valid == 1:
                        count = self.env["exhr.payslip.deductions"].search_count(
                            [
                                ("payslip_id", "=", self.id),
                                ("name_id", "=", deduction_id.id),
                            ]
                        )

                        if count == 0:
                            # nothing found
                            # will create deductions line
                            self.env["exhr.payslip.deductions"].create(
                                {
                                    "payslip_id": self.id,
                                    "name_id": deduction_id.id,
                                    "amount_total": personal_contri,
                                    "personal_contri": personal_contri,
                                    "employer_contri": 100,
                                }
                            )
                        else:
                            # existing found
                            # will update the existing amount
                            self.env["exhr.payslip.deductions"].search(
                                [
                                    ("payslip_id", "=", self.id),
                                    ("name_id", "=", deduction_id.id),
                                ]
                            ).write(
                                {
                                    "amount_total": personal_contri,
                                    "personal_contri": personal_contri,
                                    "employer_contri": 100,
                                }
                            )

                        hdmf_lines = self.env["hdmf.contribution.line"].create(
                            {
                                "payslip_id": self.id,
                                "date": self.pay_period_to,
                                "ee_amount": personal_contri,
                                "er_amount": 100,
                            }
                        )

                else:
                    raise UserError("Wage not in HDMF Contri. range")

    def compute_tax(self, amount):
        """Computes withholding tax amount for the employee depending on the
        - range of the taxable amount on the employee's payslip
        - employee's payroll type indicated on contract
        parameters:
                'amount': taxable amount of the payslip
        """
        contract = self.env["hr.contract"].search(
            [("employee_id", "=", self.employee_id.id), ("state", "in", ["open"])]
        )

        value = 0

        if contract:
            if not contract.tax_shield:
                withhold_tax_config = self.env["withholding.tax.config"].search(
                    [
                        ("range_from", "<=", amount),
                        ("range_to", ">=", amount),
                        ("payroll_type_id", "=", contract.payroll_type_id.id),
                    ],
                    limit=1,
                )

                x_value = withhold_tax_config.x_value
                y_value = withhold_tax_config.y_value
                z_value = withhold_tax_config.z_value

                if x_value == y_value == z_value == 0:
                    value = 0
                else:
                    value = x_value + ((amount - z_value) * (y_value / 100))
        return value

    def compute_payslip(self):
        for rec in self:
            # print('EMPLOYEE: ', self.employee_id.name)
            # search for contract, get only the latest one based on id of creation
            # print('EMPLOYEEEEEEEEEEEE: ', self.employee_id.name)
            data_a = self.get_contract_info(self.cutoff_date, self.employee_id.id)
            ic(data_a)
            if data_a:
                vals = self.env["hr.contract"].search(
                    [("id", "=", data_a.get("contract_id"))]
                )

                # attached attendance sheet in payslip
                ic(vals)
                rec.update_attendance_sheet()
                rec.compute_count_days(vals)
                # if self.employee_id.id == 1474:
                #     print("1")
                # earnings
                rec.compute_base_salary(vals)
                rec.compute_leave_pay(vals)
                rec.compute_holiday_pay(vals)
                rec.compute_overtime(vals)
                # if self.employee_id.id == 1474:
                #     print("1")
                # deductions
                rec.compute_tardiness(vals)
                rec.compute_undertime(vals)
                rec.compute_leave_wo_pay(vals)
                # if self.employee_id.id == 1474:
                #     print("1")
                rec.compute_sss(vals)
                rec.compute_phic(vals)
                rec.compute_hdmf(vals)
                # if self.employee_id.id == 1474:
                #     print("self.no_days_present : ", self.no_days_present)
                # others
                rec.compute_allowance(vals)
                rec.compute_loans(vals)

                base_salary = (
                    self.env["exhr.payslip.earnings"]
                    .search(
                        [
                            ("name_id.name", "=", "Base Salary"),
                            ("payslip_id", "=", rec.id),
                        ],
                        limit=1,
                    )
                    .amount_subtotal
                )
                ic(base_salary)
                if (
                    base_salary == 0
                    or self.amount_total <= 0
                    or self.no_days_present == 0
                ):
                    ic(self.amount_total)
                    ic(self.no_days_present)
                    ic(vals.work_schedule_type)
                    if vals.work_schedule_type != "na":
                        rec.unlink()
                else:
                    ic(f"{base_salary} > button_compute_payslip")
                    self.button_compute_payslip()

    def button_compute_payslip(self):
        ic("button_compute_payslip")
        for rec in self:
            ic(rec)
            # search for contract, get only the latest one based on id of creation
            data_a = self.get_contract_info(self.cutoff_date, self.employee_id.id)
            ic(data_a)
            if data_a:
                vals = self.env["hr.contract"].search(
                    [("id", "=", data_a.get("contract_id"))]
                )
                ic(vals)

                rec.update_attendance_sheet()
                rec.compute_count_days(vals)

                # earnings
                rec.compute_base_salary(vals)
                rec.compute_leave_pay(vals)
                rec.compute_holiday_pay(vals)
                rec.compute_overtime(vals)

                # deductions
                rec.compute_tardiness(vals)
                rec.compute_undertime(vals)
                rec.compute_leave_wo_pay(vals)

                for line in self.sss_ids:
                    line.unlink()
                for line in self.phic_ids:
                    line.unlink()
                for line in self.hdmf_ids:
                    line.unlink()
                for line in self.nontaxable_line_ids:
                    line.unlink()

                rec.compute_sss(vals)
                rec.compute_phic(vals)
                rec.compute_hdmf(vals)

                rec.compute_allowance(vals)
                rec.compute_loans(vals)

    def button_compute_total(self):
        for rec in self:
            rec._compute_basic()
            rec._compute_amount()

    def update_attendance_sheet(self):
        ic("update_attendance_sheet")
        attendance_obj = (
            self.env["hr.attendance.sheet"]
            .sudo()
            .search(
                [
                    ("employee_id", "=", self.employee_id.id),
                    ("date", ">=", self.pay_period_from),
                    ("date", "<=", self.pay_period_to),
                    ("active", "=", True),
                    ("original", "!=", "excess"),
                ]
            )
        )
        self.attendance_sheet_ids = attendance_obj
        ic(attendance_obj)

        for x in self.attendance_sheet_ids:
            x.update_attendance_sheet()

    def set_to_posted(self):
        if self.payroll_id:
            self.state = "posted"
            if not self.cutoff_date:
                self.posted_date = self.pay_period_to

            self.posted_date = fields.Date.context_today(self)

            if self.name == "Draft":
                self.name = self.env["ir.sequence"].next_by_code(
                    "exhr_payslip_no_sequence"
                )

            # Creates JV if auto_jv = True in Settings
            if self.payroll_id.auto_jv == True:
                self._create_account_move()

            if self.overtime_ids:
                for line in self.overtime_ids:
                    line.status = "paid"
            if self.leave_ids:
                for line in self.leave_ids:
                    line.leaves_id.payslip_status = True
        else:
            raise UserError(
                "Please check the payroll number field. The payslip should have a payroll number."
            )

    def set_to_cancel(self):
        self.state = "cancel"

        if self.overtime_ids:
            for line in self.overtime_ids:
                line.status = "approved"

        if self.leave_ids:
            for line in self.leave_ids:
                line.leaves_id.payslip_status = False

    def set_to_cancel_posted(self):
        self.state = "cancel"

        for line in self:
            if line.move_id:
                line.move_id.button_cancel()

            if line.overtime_ids:
                for l in self.overtime_ids:
                    l.status = "approved"

            if line.leave_ids:
                for l in self.leave_ids:
                    l.leaves_id.payslip_status = False

    def set_to_draft(self):
        self.state = "draft"

    def _create_account_move(self):
        move_obj = self.env["account.move"]
        move_line_obj = self.env["account.move.line"]
        val_line = []

        vals = {
            "name": self.env["ir.sequence"].next_by_code(
                "exhr_payslip_journal_no_sequence"
            ),
            "date": fields.Date.context_today(self),
            "ref": self.name,
            # 'partner_id': self.employee_id.user_id.partner_id.id,
            "partner_id": self.employee_id.partner_id.id,
            # 'journal_id': self.payroll_id.payroll_journal_id.id
            "journal_id": self.employee_id.accounting_tag_id.default_payroll_journal_id.id,
        }

        adjustment_amt = 0
        tax_amt = abs(self.amount_tax_signed) or 0

        sss = self.env["sss.contribution.line"].search([("payslip_id", "=", self.id)])
        sss_er_amt = sum(
            (line.er_regular_amount + line.er_ec_amount + line.er_mpf_amount)
            for line in sss
        )
        sss_ee_amt = sum(
            (line.ee_regular_amount + line.ee_ec_amount + line.ee_mpf_amount)
            for line in sss
        )
        sss_amt = sss_er_amt + sss_ee_amt

        phic = self.env["phic.contribution.line"].search([("payslip_id", "=", self.id)])
        phic_er_amt = sum(line.er_amount for line in phic)
        phic_ee_amt = sum(line.ee_amount for line in phic)
        phic_amt = phic_er_amt + phic_ee_amt

        hdmf = self.env["hdmf.contribution.line"].search([("payslip_id", "=", self.id)])
        hdmf_er_amt = sum(line.er_amount for line in hdmf)
        hdmf_ee_amt = sum(line.ee_amount for line in hdmf)
        hdmf_amt = hdmf_er_amt + hdmf_ee_amt

        payable_others = self.env["exhr.payslip.nontaxable"].search(
            [("payslip_id", "=", self.id), ("loan_id", "=", False)]
        )
        payable_others_amt = abs(sum(p.amount_total for p in payable_others))

        payable_amt = (
            (self.amount_untaxed or 0)
            + (self.amount_tax_signed or 0)
            + (self.amount_nontaxable_signed or 0)
        )
        loans = self.env["exhr.payslip.nontaxable"].search(
            [("payslip_id", "=", self.id), ("loan_id", "!=", False)]
        )
        loan_amt = abs(sum(loan.amount_total for loan in loans))

        salaries_exp_amt = sum(
            line.amount_subtotal for line in self.earnings_line_ids
        ) - sum(
            line.amount_total
            for line in self.deductions_line_ids
            if line.name_id.name
            not in ("SSS Contribution", "PHIC Contribution", "HDMF Contribution")
        )

        # Salaries Expense - creating move line
        if not self.employee_id.accounting_tag_id:
            raise UserError("No Accounting Tag.")

        salaries_exp_vals = {
            "account_id": self.employee_id.accounting_tag_id.default_salaries_exp_account_id.id,
            "partner_id": self.employee_id.partner_id.id,
            "analytic_account_id": self.employee_id.analytic_account_id.id or False,
            "analytic_tag_ids": [
                (6, 0, self.employee_id.analytic_account_id.analytic_tag_ids.ids)
            ]
            or False,
            "name": "Salaries Expense",
            "debit": salaries_exp_amt,
            "credit": 0,
            "balance": 0,
        }
        if salaries_exp_amt > 0:
            val_line.append((0, 0, salaries_exp_vals))

        # sss er contribution - creating move line
        sss_er_vals = {
            "account_id": self.employee_id.accounting_tag_id.default_sss_er_account_id.id,
            "partner_id": self.employee_id.partner_id.id,
            "analytic_account_id": self.employee_id.analytic_account_id.id or False,
            "analytic_tag_ids": [
                (6, 0, self.employee_id.analytic_account_id.analytic_tag_ids.ids)
            ]
            or False,
            "name": "SSS Contribution (ER)",
            "debit": sss_er_amt,
            "credit": 0,
            "balance": 0,
        }
        if sss_er_amt > 0:
            val_line.append((0, 0, sss_er_vals))

        # phic er contribution - creating move line
        phic_er_vals = {
            "account_id": self.employee_id.accounting_tag_id.default_phic_er_account_id.id,
            "partner_id": self.employee_id.partner_id.id,
            "analytic_account_id": self.employee_id.analytic_account_id.id or False,
            "analytic_tag_ids": [
                (6, 0, self.employee_id.analytic_account_id.analytic_tag_ids.ids)
            ]
            or False,
            "name": "PHIC Contribution (ER)",
            "debit": phic_er_amt,
            "credit": 0,
            "balance": 0,
        }
        if phic_er_amt > 0:
            val_line.append((0, 0, phic_er_vals))

        # hdmf er contribution - creating move line
        hdmf_er_vals = {
            "account_id": self.employee_id.accounting_tag_id.default_hdmf_er_account_id.id,
            "partner_id": self.employee_id.partner_id.id,
            "analytic_account_id": self.employee_id.analytic_account_id.id or False,
            "analytic_tag_ids": [
                (6, 0, self.employee_id.analytic_account_id.analytic_tag_ids.ids)
            ]
            or False,
            "name": "HDMF Contribution (ER)",
            "debit": hdmf_er_amt,
            "credit": 0,
            "balance": 0,
        }
        if hdmf_er_amt > 0:
            val_line.append((0, 0, hdmf_er_vals))

        # withholding tax - creating move line
        tax_vals = {
            "account_id": self.employee_id.accounting_tag_id.default_tax_account_id.id,
            "partner_id": self.employee_id.partner_id.id,
            "analytic_account_id": self.employee_id.analytic_account_id.id or False,
            "analytic_tag_ids": [
                (6, 0, self.employee_id.analytic_account_id.analytic_tag_ids.ids)
            ]
            or False,
            "name": "Withholding Tax Payable",
            "debit": 0,
            "credit": tax_amt,
            "balance": 0,
        }
        if tax_amt > 0:
            val_line.append((0, 0, tax_vals))

        # sss contribution - creating move line
        sss_vals = {
            "account_id": self.employee_id.accounting_tag_id.default_sss_account_id.id,
            "partner_id": self.employee_id.partner_id.id,
            "analytic_account_id": self.employee_id.analytic_account_id.id or False,
            "analytic_tag_ids": [
                (6, 0, self.employee_id.analytic_account_id.analytic_tag_ids.ids)
            ]
            or False,
            "name": "SSS Contribution Payable",
            "debit": 0,
            "credit": sss_amt,
            "balance": 0,
        }
        if sss_amt > 0:
            val_line.append((0, 0, sss_vals))

        # phic contribution - creating move line
        phic_vals = {
            "account_id": self.employee_id.accounting_tag_id.default_phic_account_id.id,
            "partner_id": self.employee_id.partner_id.id,
            "analytic_account_id": self.employee_id.analytic_account_id.id or False,
            "analytic_tag_ids": [
                (6, 0, self.employee_id.analytic_account_id.analytic_tag_ids.ids)
            ]
            or False,
            "name": "PHIC Contribution Payable",
            "debit": 0,
            "credit": phic_amt,
            "balance": 0,
        }
        if phic_amt > 0:
            val_line.append((0, 0, phic_vals))

        # hdmf contribution - creating move line
        hdmf_vals = {
            "account_id": self.employee_id.accounting_tag_id.default_hdmf_account_id.id,
            "partner_id": self.employee_id.partner_id.id,
            "analytic_account_id": self.employee_id.analytic_account_id.id or False,
            "analytic_tag_ids": [
                (6, 0, self.employee_id.analytic_account_id.analytic_tag_ids.ids)
            ]
            or False,
            "name": "HDMF Contribution Payable",
            "debit": 0,
            "credit": hdmf_amt,
            "balance": 0,
        }
        if hdmf_amt > 0:
            val_line.append((0, 0, hdmf_vals))

        # CRF
        for p in self.nontaxable_line_ids:
            if p.amount_total >= 0:
                dr = abs(p.amount_total)
                cr = 0
            if p.amount_total < 0:
                dr = 0
                cr = abs(p.amount_total)
            payable_others_vals = {
                "account_id": p.gl_account_id.id,
                "partner_id": self.employee_id.partner_id.id,
                "analytic_account_id": self.employee_id.analytic_account_id.id or False,
                "analytic_tag_ids": [
                    (6, 0, self.employee_id.analytic_account_id.analytic_tag_ids.ids)
                ]
                or False,
                "name": p.ref,
                "debit": dr,
                "credit": cr,
                "balance": 0,
            }
            if dr > 0:
                val_line.append((0, 0, payable_others_vals))
            elif cr > 0:
                val_line.append((0, 0, payable_others_vals))

        # salaries - creating move line
        payable_vals = {
            "account_id": self.employee_id.accounting_tag_id.default_net_pay_account_id.id,
            "partner_id": self.employee_id.partner_id.id,
            "analytic_account_id": self.employee_id.analytic_account_id.id or False,
            "analytic_tag_ids": [
                (6, 0, self.employee_id.analytic_account_id.analytic_tag_ids.ids)
            ]
            or False,
            "name": "Net Pay",
            "debit": 0,
            "credit": payable_amt,
            "balance": 0,
        }
        if payable_amt > 0:
            val_line.append((0, 0, payable_vals))

        vals["line_ids"] = val_line

        am_id = move_obj.create(vals)
        self.move_id = am_id.id

        # Auto-posts the created JV if auto_post = True in Settings
        if self.payroll_id.auto_post:
            am_id.post()

    # UNSUSED FUNCTION
    def compute_ot_night_diff(self, ot_st, ot_end, att_date):
        attsheet = (
            self.env["hr.attendance.sheet"]
            .sudo()
            .search(
                [("employee_id", "=", self.employee_id.id), ("date", "=", att_date)]
            )
        )
        nd_start = attsheet.ns_start
        nd_end = attsheet.ns_end
        nd_ot_hr = 0
        if ot_end >= nd_start:
            # Ended before midnight
            if ot_st <= nd_start:
                # started before night diff
                nd_ot_hr += ot_end - nd_start
            else:
                nd_ot_hr += ot_end - ot_st

        elif ot_end < nd_start and ot_st > nd_end:
            # ended beyond midnight
            # nd_ot_hr+= 24-ot_start
            if ot_st <= nd_start:
                # started before night diff
                nd_ot_hr += 24 - nd_start
            else:
                nd_ot_hr += 24 - ot_st

            if ot_end >= nd_end:
                nd_ot_hr += nd_end
            else:
                nd_ot_hr += ot_end

        elif ot_st < nd_end:
            if ot_end > nd_end:
                nd_ot_hr += nd_end
            else:
                nd_ot_hr += ot_end - ot_st
        return nd_ot_hr

    # UNSUSED FUNCTION
    def apply_changes(self):
        nightdiff_amount_pay = 0
        holiday_amount_pay = 0
        tardiness_amount_ded = 0
        undertime_amount_ded = 0
        leavewopay_amount_ded = 0

        if self.attendance_sheet_ids:
            for x in self.attendance_sheet_ids:
                nightdiff_amount_pay += x.nightdiff_amount_pay
                holiday_amount_pay += x.holiday_amount_pay
                tardiness_amount_ded += x.tardiness_amount_ded
                undertime_amount_ded += x.undertime_amount_ded
                leavewopay_amount_ded += x.leavewopay_amount_ded

            self.env["exhr.payslip.earnings"].search(
                [
                    ("payslip_id", "=", self.id),
                    ("name_id.name", "=", "Night Differential"),
                ]
            ).write({"amount_subtotal": nightdiff_amount_pay})
            self.env["exhr.payslip.earnings"].search(
                [("payslip_id", "=", self.id), ("name_id.name", "=", "Holiday Pay")]
            ).write({"amount_subtotal": holiday_amount_pay})
            self.env["exhr.payslip.deductions"].search(
                [("payslip_id", "=", self.id), ("name_id.name", "=", "Tardiness")]
            ).write({"amount_total": tardiness_amount_ded})
            self.env["exhr.payslip.deductions"].search(
                [("payslip_id", "=", self.id), ("name_id.name", "=", "Undertime")]
            ).write({"amount_total": undertime_amount_ded})
            self.env["exhr.payslip.deductions"].search(
                [("payslip_id", "=", self.id), ("name_id.name", "=", "Leave w/o pay")]
            ).write({"amount_total": leavewopay_amount_ded})

    # UNSUSED FUNCTION
    def compute_night_differential(self, vals):
        if vals:
            # with contract
            # will update the payslip base on the found contract
            if (
                self.env["earnings.type"].search_count(
                    [("name", "=", "Night Differential"), ("active", "=", True)]
                )
                > 0
            ):
                earning_id = self.env["earnings.type"].search(
                    [("name", "=", "Night Differential"), ("active", "=", True)],
                    limit=1,
                )

                count = self.env["exhr.payslip.earnings"].search_count(
                    [("payslip_id", "=", self.id), ("name_id", "=", earning_id.id)]
                )

                if count == 0:
                    # nothing found
                    # will create earnings line
                    # self.env['exhr.payslip.earnings'].create({'payslip_id':self.id,'name_id':earning_id.id,'amount_subtotal': nightdiff_amount_pay,'no_day_hrs':nightdiff_hrs})
                    self.env["exhr.payslip.earnings"].create(
                        {
                            "payslip_id": self.id,
                            "name_id": earning_id.id,
                            "amount_subtotal": 0,
                            "no_day_hrs": "",
                        }
                    )
                else:
                    # existing found
                    # will update the existing amount
                    # self.env['exhr.payslip.earnings'].search([('payslip_id','=',self.id),('name_id','=',earning_id.id)]).write({'amount_subtotal': nightdiff_amount_pay,'no_day_hrs':nightdiff_hrs})
                    self.env["exhr.payslip.earnings"].search(
                        [("payslip_id", "=", self.id), ("name_id", "=", earning_id.id)]
                    ).write({"amount_subtotal": 0, "no_day_hrs": ""})

            else:
                raise UserError(
                    "No Night Differential found on earnings configuration."
                )

        else:
            raise UserError("No Running Contract found!")

    def unlink(self):
        # for rec in self:
        #     rec.state = "inactive"

        ic("unlinked")
        return super(exhr_payslip, self).unlink()
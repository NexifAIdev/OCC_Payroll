# -*- coding: utf-8 -*-
# Native Python modules
from datetime import datetime, date, timedelta
import time
import calendar

# Local python modules

# Custom python modules
import pytz

# Odoo modules
from odoo import models, fields, api, _
from odoo.tools.translate import _
from odoo.exceptions import UserError, ValidationError


class OccPayrollCfg(models.AbstractModel):
    _name = "occ.payroll.cfg"
    _description = "Payroll Config"

    # manual.attendance
    # pre.overtime.request
    # overtime.request
    # hr.attendance.sheet
    # res.config.settings
    # schedule.type
    # hr.attendance.sheet
    # dialog.attendance.sheet
    # hr.attendance
    # custom.holidays.config
    # custom.holidays
    # hr.leave.type
    # hr.attendance.sheet.summary
    # overtime.request.line

    DEFAULT_SERVER_DATE_FORMAT = "%Y-%m-%d"
    DEFAULT_SERVER_DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
    manila_tz = pytz.timezone("Asia/Manila")

    state_list = [
        ("draft", "Draft"),
        ("submitted", "Submitted"),  # approver 1
        ("subver", "Submitted"),  # approver 1 or approver 2
        ("verified", "Verified"),  # approver 2
        ("approved", "Approved"),
        ("denied", "Denied"),
        ("cancelled", "Cancel"),
    ]
    state_list2 = [
        ("draft", "Draft"),
        ("submitted", "Submitted"),  # approver 1
        ("subver", "Submitted"),  # approver 1 or approver 2
        ("verified", "Verified"),  # approver 2
        ("approved", "Done"),
        ("denied", "Denied"),
        ("cancelled", "Cancel"),
    ]

    list_policy = [
        ("1", "Pre-approved OT request before Filing actual OT request"),
        ("2", "OT Request only"),
    ]

    list_approval = [
        ("1", "Approver 1 and Approver 2 before it approves"),
        ("2", "Approver 1 or Approver 2 before it approves"),
        ("3", "Approver 1 only before it approves"),
        ("4", "Approver 2 only before it approves"),
    ]

    odoo_dow_list = [
        ("0", "Monday"),
        ("1", "Tuesday"),
        ("2", "Wednesday"),
        ("3", "Thursday"),
        ("4", "Friday"),
        ("5", "Saturday"),
        ("6", "Sunday"),
    ]

    ratetype_list = [
        ("0", "Ordinary Day"),
        ("1", "Rest Day"),
        ("2", "Special Day"),
        ("3", "Special day falling on rest day"),
        ("4", "Regular Holiday"),
        ("5", "Regular Holiday falling on rest day"),
        ("6", "Double Holiday"),
        ("7", "Double Holiday falling on rest day"),
        ("8", "Ordinary Day, night shift"),
        ("9", "Rest Day, night shift"),
        ("10", "Special Day, night shift"),
        ("11", "Special Day, rest day, night shift"),
        ("12", "Regular Holiday, night shift"),
        ("13", "Regular Holiday, rest day, night shift"),
        ("14", "Double Holiday, night shift"),
        ("15", "Double Holiday, rest day, night shift"),
        ("16", "Ordinary day, overtime"),
        ("17", "Rest day, overtime"),
        ("18", "Special day, overtime"),
        ("19", "Special day, rest day, overtime"),
        ("20", "Regular Holiday, overtime"),
        ("21", "Regular Holiday, rest day, overtime"),
        ("22", "Double Holiday, overtime"),
        ("23", "Double Holiday, rest day, overtime"),
        ("24", "Ordinary Day, night shift, OT"),
        ("25", "Rest Day, night shift, OT"),
        ("26", "Special Day, night shift, OT"),
        ("27", "Special Day, rest day, night shift, OT"),
        ("28", "Regular Holiday, night shift, OT"),
        ("29", "Regular Holiday, rest day, night shift, OT"),
        ("30", "Double Holiday, night shift, OT"),
        ("31", "Double Holiday, rest day, night shift, OT"),
    ]

    def get_holiday_status(self, date_now, work_location):
        """
        This function returns the type and number of holidays for the given date
        param: date, work_location
        return: count, type
        """
        val_dict = {"count": 0, "type": None}
        holiday = self.env["custom.holidays"].search(
            [
                "&",
                "&",
                ("date", "=", date_now),
                ("state", "=", "active"),
                "|",
                ("work_location_id", "=", work_location.id),
                ("work_location_id", "=", False),
            ],
            limit=1,
        )
        holiday_count = self.env["custom.holidays"].search_count(
            [
                "&",
                "&",
                ("date", "=", date_now),
                ("state", "=", "active"),
                "|",
                ("work_location_id", "=", work_location.id),
                ("work_location_id", "=", False),
            ]
        )
        if holiday:
            val_dict["count"] = holiday_count
            val_dict["type"] = holiday.holiday_type

        return val_dict

    def get_attendance_sched(self, date_now, resource_calendar_id, work_location):
        """
        this function returns a dictionary of planned_in, planned_out, break_hours based on the schedule of employee in contracts (resource.calendar)
        - if with work adjustment for the specified date, the planned_in and planned_out is based on the validated work schedule adjustment
        param: date, resource_calendar_id
        return: planned_in, planned_out, break_hours
        """
        hour_from = 0
        hour_to = 0
        break_hours = 1

        if date_now and resource_calendar_id:
            dow_int = date_now.weekday()
            if dow_int == -1:
                dow_int = 6
            calendar_line = self.env["resource.calendar.attendance"].search(
                [
                    "|",
                    "&",
                    ("calendar_id", "=", resource_calendar_id.id),
                    "&",
                    ("dayofweek", "=", str(dow_int)),
                    "&",
                    ("date_from", "<=", self.date),
                    ("date_to", ">=", self.date),
                    "&",
                    ("calendar_id", "=", resource_calendar_id.id),
                    "&",
                    ("dayofweek", "=", str(dow_int)),
                    "&",
                    ("date_from", "=", False),
                    ("date_to", "=", False),
                ],
                order="date_from asc",
                limit=1,
            )

            if calendar_line:
                hour_from = calendar_line.hour_from
                hour_to = calendar_line.hour_to
                break_hours = calendar_line.break_hours

            work_adj = self.env["work.sched.adjustment"].search(
                [
                    ("employee_id", "=", self.employee_id.id),
                    ("date_change", "=", self.date),
                    ("status", "=", "validate"),
                ],
                order="create_date desc",
                limit=1,
            )

            if work_adj:
                hour_from = work_adj.planned_in
                hour_to = work_adj.planned_out

            val_dict = {
                "planned_in": hour_from,
                "planned_out": hour_to,
                "break_hours": break_hours,
            }

        return val_dict

    def get_attendance_type(
        self,
        date_now,
        dow_int,
        planned_in,
        planned_out,
        actual_in,
        actual_out,
        ns_start,
        ns_end,
        work_location,
    ):
        """
        Returns the Type field in hr.attendance.sheet
        - Ordinary Day
        - Rest Day
        - Special Day
        - Regular Holiday
        """
        attype = "0"  # Ordinary Day
        holiday_status = self.get_holiday_status(date_now, work_location)

        # FOR REGULAR WORKING SCHEDULE
        if planned_in == planned_out:  # if planned_in=0, planned_out=0
            attype = "1"  # Rest Day
            if holiday_status.get("count") == 0:
                attype = "1"  # Rest Day

                if planned_in >= ns_start and planned_out <= ns_end:
                    attype = "9"  # Rest Day, night shift

            elif holiday_status.get("count") == 1:
                if holiday_status.get("type") == "special":
                    attype = "3"  # Special day falling on rest day

                    if planned_in >= ns_start and planned_out <= ns_end:
                        attype = "11"  # Special Day, rest day, night shift

                elif holiday_status.get("type") == "regular":
                    attype = "5"  # Regular Holiday falling on rest day

                    if planned_in >= ns_start and planned_out <= ns_end:
                        attype = "13"  # Regular Holiday, rest day, night shift

            elif holiday_status.get("count") == 2 or holiday_status.get("count") > 2:
                attype = "7"  # Double Holiday falling on rest day

                if planned_in >= ns_start and planned_out <= ns_end:
                    attype = "15"  # Double Holiday, rest day, night shift

        else:  # with attendance
            attype = "0"  # Ordinary Day
            if holiday_status.get("count") == 0:
                attype = "0"  # Ordinary Day
                if (
                    (
                        (planned_in >= ns_start and planned_in < 24)
                        or (planned_out >= ns_start and planned_out < 24)
                        or planned_out <= ns_end
                    )
                    and planned_out != 0
                    and planned_in != 0
                    and actual_in != 0
                    and actual_out != 0
                ):
                    attype = "8"  # Ordinary Day, night shift

            elif holiday_status.get("count") == 1:  # one holiday
                if holiday_status.get("type") == "special":
                    attype = "2"  # Special Day

                    if planned_in >= ns_start and planned_out <= ns_end:
                        attype = "10"  # Special Day, night shift

                elif holiday_status.get("type") == "regular":
                    attype = "4"  # Regular Holiday

                    if planned_in >= ns_start and planned_out <= ns_end:
                        attype = "12"  # Regular Holiday, night shift

            elif holiday_status.get("count") == 2 or holiday_status.get("count") > 2:
                attype = "6"  # Double Holiday

                if planned_in >= ns_start and planned_out <= ns_end:
                    attype = "14"  # Double Holiday, night shift

        return attype

    def get_count_work_days(self, date_now, dow_int, work_location):
        """This function returns if the given date is counted as a work day
        -Sundays and holidays are not working days (as per AVSC policy)
        """
        attype = 1
        holiday_status = self.get_holiday_status(date_now, work_location)
        contract = self.env["hr.contract"].search(
            [("employee_id", "=", self.employee_id.id), ("state", "=", "open")], limit=1
        )

        if dow_int == 6 and contract.daily_wage == "ww":  # sunday
            attype = 0
        else:
            att_list = self.env["hr.attendance.sheet"].search(
                [
                    ("employee_id", "=", self.employee_id.id),
                    ("payslip_id", "=", self.id),
                    ("date", "=", date_now),
                ],
                limit=1,
            )
            if att_list.rate_type == "1":
                attype = 0
            elif att_list.rate_type == 1:
                attype = 0

        if holiday_status.get("count") > 0:
            attype = 0

        return attype

    def new_count_work_days(self, date_now, dow_int, work_location):
        """This function returns if the given date is counted as a work day
        -Sundays and holidays are not working days (as per AVSC policy)
        """
        attype = 1
        holiday_status = self.get_holiday_status(date_now, work_location)

        # shane
        day_type = (
            self.env["hr.attendance.sheet"]
            .search(
                [("employee_id", "=", self.employee_id.id), ("date", "=", date_now)],
                limit=1,
            )
            .rate_type
        )

        if day_type not in ("0", "8", "16", "24"):
            attype = 0

        # if dow_int == 6: #sunday
        # 	attype = 0

        if holiday_status.get("count") > 0:
            attype = 0

        return attype

    def get_holiday_pay(self, date_now, dow_int, work_location, contract):
        """This function returns if the given date is a holiday"""
        attype = 0
        holidays = self.get_holiday_status(date_now, work_location)

        if holidays.get("count") > 0:
            attype = 1

        return attype

    def get_contract_info(self, my_date, employee_id):
        """This function returns the running contract of the employee
        return: hourly_rate,daily_rate,hours,contract_id
        """
        contract = self.env["hr.contract"].search(
            [
                "&",
                "&",
                "&",
                ("employee_id", "=", employee_id),
                ("date_start", "<=", my_date),
                ("state", "=", "open"),
                "|",
                ("date_end", ">=", my_date),
                ("date_end", "=", None),
            ]
        )

        if len(contract) == 0:
            raise UserError("No Running Contract found!")

        return {
            "hourly_rate": contract.hourly_rate,
            "daily_rate": contract.daily_rate,
            "hours": contract.eemr_hours,
            "contract_id": contract.id,
        }

    def get_work_time(self, resource_calendar_id, date_now):
        if resource_calendar_id:
            query = """
                SELECT
                    COALESCE(
                        (
                            SELECT hour_from FROM resource_calendar_attendance
                            WHERE calendar_id = a.calendar_id
                            AND dayofweek::INT = a.dow
                            AND a.day::DATE
                            BETWEEN date_from::DATE AND date_to::DATE
                            ORDER BY id DESC
                            LIMIT 1
                        )
                        ,
                        (
                            COALESCE(
                                (
                                    SELECT hour_from FROM resource_calendar_attendance
                                    WHERE calendar_id = a.calendar_id
                                    AND dayofweek::INT = a.dow
                                    AND year::INT = EXTRACT(YEAR FROM a.day)
                                    AND month::INT = EXTRACT(MONTH FROM a.day)
                                    ORDER BY id DESC
                                    LIMIT 1
                                ),
                                (
                                    COALESCE(
                                        (
                                            SELECT hour_from FROM resource_calendar_attendance
                                            WHERE calendar_id = a.calendar_id
                                            AND dayofweek::INT = a.dow
                                            AND year is null
                                            AND month::INT = EXTRACT(MONTH FROM a.day)
                                            ORDER BY id DESC
                                            LIMIT 1
                                        ),
                                        (
                                            COALESCE(
                                                (
                                                    SELECT hour_from FROM resource_calendar_attendance
                                                    WHERE calendar_id = a.calendar_id
                                                    AND dayofweek::INT = a.dow
                                                    AND year::INT = EXTRACT(YEAR FROM a.day)
                                                    AND month is null
                                                    ORDER BY id DESC
                                                    LIMIT 1
                                                ),
                                                (
                                                    COALESCE(
                                                        (
                                                            SELECT hour_from FROM resource_calendar_attendance
                                                            WHERE calendar_id = a.calendar_id
                                                            AND dayofweek::INT = a.dow
                                                            AND year is null
                                                            AND month is null
                                                            AND date_from is null
                                                            AND date_to is null
                                                            ORDER BY id DESC
                                                            LIMIT 1
                                                        ),
                                                        (
                                                        0.00
                                                        )
                                                    )
                                                )
                                            )
                                        )
                                    )
                                )
                            )
                        )
                    ) as hour_from,
                    COALESCE(
                        (
                            SELECT hour_to FROM resource_calendar_attendance
                            WHERE calendar_id = a.calendar_id
                            AND dayofweek::INT = a.dow
                            AND a.day::DATE
                            BETWEEN date_from::DATE AND date_to::DATE
                            ORDER BY id DESC
                            LIMIT 1
                        )
                        ,
                        (
                            COALESCE(
                                (
                                    SELECT hour_to FROM resource_calendar_attendance
                                    WHERE calendar_id = a.calendar_id
                                    AND dayofweek::INT = a.dow
                                    AND year::INT = EXTRACT(YEAR FROM a.day)
                                    AND month::INT = EXTRACT(MONTH FROM a.day)
                                    ORDER BY id DESC
                                    LIMIT 1
                                ),
                                (
                                    COALESCE(
                                        (
                                            SELECT hour_to FROM resource_calendar_attendance
                                            WHERE calendar_id = a.calendar_id
                                            AND dayofweek::INT = a.dow
                                            AND year is null
                                            AND month::INT = EXTRACT(MONTH FROM a.day)
                                            ORDER BY id DESC
                                            LIMIT 1
                                        ),
                                        (
                                            COALESCE(
                                                (
                                                    SELECT hour_to FROM resource_calendar_attendance
                                                    WHERE calendar_id = a.calendar_id
                                                    AND dayofweek::INT = a.dow
                                                    AND year::INT = EXTRACT(YEAR FROM a.day)
                                                    AND month is null
                                                    ORDER BY id DESC
                                                    LIMIT 1
                                                ),
                                                (
                                                    COALESCE(
                                                        (
                                                            SELECT hour_to FROM resource_calendar_attendance
                                                            WHERE calendar_id = a.calendar_id
                                                            AND dayofweek::INT = a.dow
                                                            AND year is null
                                                            AND month is null
                                                            AND date_from is null
                                                            AND date_to is null
                                                            ORDER BY id DESC
                                                            LIMIT 1
                                                        ),
                                                        (
                                                        0.00
                                                        )
                                                    )
                                                )
                                            )
                                        )
                                    )
                                )
                            )
                        )
                    ) as hour_to
                    
                FROM
                (
                    SELECT
                        (
                            %s
                        ) as calendar_id,
                        i::date AS day,
                        (
                        CASE EXTRACT(DOW FROM i)
                        WHEN 0 THEN 6
                        WHEN 1 THEN 0
                        WHEN 2 THEN 1
                        WHEN 3 THEN 2
                        WHEN 4 THEN 3
                        WHEN 5 THEN 4
                        WHEN 6 THEN 5
                        END
                        ) as dow,
                        to_char(i::timestamp, 'Day') AS date_name

                    FROM     generate_series( ('%s'::timestamp + interval '8 hours')::date, ('%s'::timestamp + interval '8 hours')::date, '1 day'::interval) i
                    ORDER BY i
                ) as a
                """ % (
                resource_calendar_id,
                date_now,
                date_now,
            )
        else:
            raise UserError(_("""No assigned Working Time for Employee"""))

        self._cr.execute(query)
        data = self._cr.fetchall()
        if data:  # for possible revision
            for x in data:
                val_dict = {
                    "planned_in": x[0],
                    "planned_out": x[1],
                }

                return val_dict

    def get_attedance_type(
        self,
        date_now,
        dow_int,
        planned_in,
        planned_out,
        ns_start,
        ns_end,
        total_ot_hrs,
        work_location,
    ):
        print(
            "Get OT Type",
            date_now,
            dow_int,
            planned_in,
            planned_out,
            ns_start,
            ns_end,
            total_ot_hrs,
        )
        # Get Work Table
        active_contract = (
            self.env["hr.contract"]
            .search(
                [
                    ("employee_id", "=", self.employee_id.id),
                    ("state", "in", ["open", "pending"]),
                ],
                order="id desc",
                limit=1,
            )
            .resource_calendar_id.id
        )
        # active_contract = self.env['hr.employee'].search([('id','=',self.employee_id.id)], limit=1).resource_calendar_id.id

        print("active_contract : ", active_contract)
        print("self.employee_id.id : ", self.employee_id.id)
        contract = self.get_holiday_status(active_contract, date_now)
        attype = "0"
        holiday_status = self.get_holiday_status(date_now, work_location)
        # 00:00 -- 00:00
        if contract["planned_in"] == 0:
            # rest day
            attype = "1"
            # check holiday: holiday type to check - regular and special
            if holiday_status.get("count") == 0:
                # rest day
                if total_ot_hrs > 8:
                    attype = "17"
                else:
                    attype = "1"

                # if planned_in >= ns_start and planned_out <= ns_end:
                if planned_out > ns_start or planned_out <= ns_end:
                    if total_ot_hrs > 8:
                        attype = "25"

                    # rest day, night shift
                    else:
                        attype = "9"

            elif holiday_status.get("count") == 1:
                # one holiday
                if holiday_status.get("type") == "special":
                    if total_ot_hrs > 8:
                        attype = "19"
                    else:
                        # special holiday, rest day
                        attype = "3"

                    # if planned_in >= ns_start and planned_out <= ns_end:
                    if planned_out > ns_start or planned_out <= ns_end:
                        if total_ot_hrs > 8:
                            attype = "27"
                        else:
                            # special holiday, rest day, night shift
                            attype = "11"

                elif holiday_status.get("type") == "regular":
                    if total_ot_hrs > 8:
                        attype = "21"
                    else:
                        # regular holiday, rest day
                        attype = "5"

                    # if planned_in >= ns_start and planned_out <= ns_end:
                    if planned_out > ns_start or planned_out <= ns_end:
                        if total_ot_hrs > 8:
                            attype = "29"
                        else:
                            # regular holiday, rest day, night shift
                            attype = "13"

            elif holiday_status.get("count") == 2 or holiday_status.get("count") > 2:
                if total_ot_hrs > 8:
                    attype = "23"
                else:
                    # double holiday, rest day
                    attype = "7"

                # if planned_in >= ns_start and planned_out <= ns_end:
                if planned_out > ns_start or planned_out <= ns_end:
                    if total_ot_hrs > 8:
                        attype = "31"
                    else:
                        # double holiday, rest day, night shift
                        attype = "15"

        else:
            # ordinary day
            # attype = '0'
            attype = "16"

            # check holiday: holiday type to check - regular and special
            if holiday_status.get("count") == 0:
                # ordinary day
                # attype = '0'
                attype = "16"
                # if planned_in >= ns_start and planned_out <= ns_end:
                if planned_out > ns_start or planned_out <= ns_end:
                    # ordinary day, night shift
                    attype = "24"

            elif holiday_status.get("count") == 1:
                # one holiday
                if holiday_status.get("type") == "special":
                    # special holiday
                    if total_ot_hrs > 8:
                        attype = "18"
                    else:
                        attype = "2"

                    # if planned_in >= ns_start and planned_out <= ns_end:
                    if planned_out > ns_start or planned_out <= ns_end:
                        if total_ot_hrs > 8:
                            attype = "26"
                        else:
                            # special holiday, night shift
                            attype = "10"

                elif holiday_status.get("type") == "regular":
                    # regular holiday
                    if total_ot_hrs > 8:
                        attype = "20"
                    else:
                        attype = "4"

                    # if planned_in >= ns_start and planned_out <= ns_end:
                    if planned_out > ns_start or planned_out <= ns_end:
                        if total_ot_hrs > 8:
                            attype = "28"
                        else:
                            # regular holiday, night shift
                            attype = "12"

            elif holiday_status.get("count") == 2 or holiday_status.get("count") > 2:
                # double holiday
                if total_ot_hrs > 8:
                    attype = "22"
                else:
                    attype = "6"

                # if planned_in >= ns_start and planned_out <= ns_end:
                if planned_out > ns_start or planned_out <= ns_end:
                    if total_ot_hrs > 8:
                        attype = "30"
                    else:
                        # double holiday, night shift
                        attype = "14"

        return attype

    def get_attendance_status(
        self,
        date,
        work_hr,
        half_work_hr,
        planned_in,
        planned_out,
        actual_in,
        actual_out,
        work_schedule_type,
        rate_type,
        work_location,
    ):
        """
        Returns the Status field in hr.attendance.sheet
        - 1 Absent
        - 2 On Leave (Half-day)
        - 3 No Time-Out
        - 4 On Leave
        - 5 Absent (Half-day)
        - 6 No Time-In
        - 7 Holiday
        """
        value = ""

        # REGULAR WORKING SCHEDULE
        if work_schedule_type == "regular":
            if planned_in > 0.0 and planned_out > 0.0:  #
                if actual_in == 0.0 and actual_out > 0.0:
                    # No Time-IN
                    value = "6"
                elif actual_out == 0.0 and actual_in > 0.0:
                    # No Time-OUT
                    value = "3"
                elif actual_in == 0.0 and actual_out == 0.0:
                    # Absent
                    value = "1"

                else:
                    if actual_out > actual_in:  # ordinary day
                        if actual_out > planned_out:
                            actual_out_biased = planned_out
                        else:
                            actual_out_biased = actual_out

                        if actual_out_biased - actual_in <= 5:  # Ordinary
                            # Absent Half-day, Ordinary day
                            if actual_out_biased - actual_in > 0:
                                value = "5"
                            else:
                                value = "1"

                        elif (
                            work_hr - (actual_out_biased - actual_in) > half_work_hr
                        ):  # Ordinary
                            # Absent, Ordinary day
                            value = "1"
                    else:  # night shift
                        if actual_in < planned_in:
                            actual_in_biased = planned_in
                        else:
                            actual_in_biased = actual_in
                        if actual_in_biased - actual_out <= 5:  # Night Shift
                            # Absent Half-day, Night Shift
                            value = "5"
                        elif (
                            work_hr - (actual_in_biased - actual_out) > half_work_hr
                        ):  # Night Shift
                            # Absent, Night Shift
                            value = "1"

        if work_schedule_type == "ww" or work_schedule_type == "fixed":
            if actual_out == 0.0 and actual_in > 0.0:
                value = "3"  # No Time-OUT
            elif (
                actual_in == 0.0
                and actual_out == 0.0
                and rate_type not in ["1", "9", "17", "25"]
            ):  # not rest day, no attendance
                value = "1"  # Absent

        holiday_status = self.get_holiday_status(date, work_location)
        if holiday_status.get("count") > 0:
            value = "7"

        # leave(half-day) - chame
        leave_half_day = self.env["hr.leave"].search(
            [
                ("employee_id", "=", self.employee_id.id),
                ("date_from", "<=", self.date),
                ("date_to", ">=", self.date),
                ("request_unit_half", "=", True),
                ("state", "=", "validate"),
            ]
        )
        if leave_half_day:
            value = "2"

        leave_whole_day = self.env["hr.leave"].search(
            [
                ("employee_id", "=", self.employee_id.id),
                ("date_from", "<=", self.date),
                ("date_to", ">=", self.date),
                ("request_unit_half", "=", False),
                ("state", "=", "validate"),
            ]
        )
        if leave_whole_day:
            value = "4"
            self.leave_start = self.planned_in
            self.leave_end = self.planned_out

        return value

    def get_attendance_remarks(self, employee_id, date_from, date_to):
        value = self.remarks
        leaves = self.env["hr.leave"].search(
            [
                ("employee_id", "=", employee_id.id),
                ("date_from", "<=", date_from),
                ("date_to", ">=", date_to),
                ("state", "=", "validate"),
            ]
        )
        if leaves:
            value = ""
            for l in leaves:
                value += l.holiday_status_id.name

        return value

    def get_attendance_actual(self):
        """
        This function populates the actual in and actual out in hr.attendance.sheet
        """
        in_hr = 0
        out_hr = 0

        attendance_query = """
            SELECT
                ha.next_day_checkout,
                (
                    SELECT ins.check_in FROM hr_attendance ins
                    WHERE ins.check_in_date::DATE = '%s'::DATE AND ins.employee_id = %s
                    ORDER BY ins.check_in ASC NULLS LAST LIMIT 1
                ) AS cin,
                ha.check_out AS cout
            FROM hr_attendance ha
            WHERE ha.check_in_date::DATE = '%s'::DATE
            AND ha.employee_id = %s
            ORDER BY ha.check_out DESC NULLS LAST
            LIMIT 1
        """ % (
            self.date,
            self.employee_id.id,
            self.date,
            self.employee_id.id,
        )
        self._cr.execute(attendance_query)
        attendance_obj = self._cr.fetchall()
        if attendance_obj:

            if attendance_obj[0][1]:
                obj_check_in = attendance_obj[0][1]

                in_hr = int(obj_check_in.astimezone(self.manila_tz).strftime("%-H"))
                in_min = int(obj_check_in.astimezone(self.manila_tz).strftime("%-M"))

                actual_in_dt = obj_check_in.astimezone(self.manila_tz)

                if in_min > 0:
                    in_hr = in_hr + (in_min / 60)

            if attendance_obj[0][2]:
                obj_check_out = attendance_obj[0][2]
                out_hr = int(obj_check_out.astimezone(self.manila_tz).strftime("%-H"))
                out_min = int(obj_check_out.astimezone(self.manila_tz).strftime("%-M"))

                actual_out_dt = obj_check_out.astimezone(self.manila_tz)

                if out_min > 0:
                    out_hr = out_hr + (out_min / 60)

            if self.original != "excess":
                if attendance_obj[0][1]:
                    self.write({"actual_in": in_hr})
                if attendance_obj[0][2]:
                    if attendance_obj[0][0] == True:
                        self.write({"actual_out": 24})
                    else:
                        self.write({"actual_out": out_hr})

            if attendance_obj[0][0] == True:
                if self.original == "original":
                    if self.original != "excess":
                        self.copy().write(
                            {
                                "original": "excess",
                                "actual_in": 0,
                                "actual_out": out_hr,
                                "date": datetime.strptime(str(self.date), "%Y-%m-%d")
                                + timedelta(days=1),
                            }
                        )
                        self.actual_out = 24
                        self.original = "modified"

        # * [07/17/2024] Added import attendance

        # Format the date for clockify
        split_date = self.date.strftime("%Y-%m-%d").split("-")
        date_format_clockify = f"{split_date[1]},{split_date[2]},{split_date[0]}"

        import_attendance_clockify = self.env["hr.import.attendance.line"].search(
            [
                ("date_from", "=", date_format_clockify),
                ("employee_id", "=", self.employee_id.id),
            ],
            order="write_date asc",
        )
        import_attendance_biometrics = self.env[
            "hr.import.attendance.line"
        ].search(
            [("date_from", "=", self.date), ("employee_id", "=", self.employee_id.id)],
            order="write_date asc",
        )

        if import_attendance_clockify:
            for iac in import_attendance_clockify.filtered(
                lambda x: x.employee_attendance_id.state == "validated"
            ):
                time_in = datetime.strptime(iac.hour_from, "%H:%M:%S").time()
                # Calculate the total number of seconds since midnight
                total_in_seconds = (
                    time_in.hour * 3600 + time_in.minute * 60 + time_in.second
                )
                # Calculate the float value from 0 to 24
                time_in_float = total_in_seconds / 3600

                self.actual_in = time_in_float

                time_out = datetime.strptime(iac.hour_from, "%H:%M:%S").time()
                # Calculate the total number of seconds since midnight
                total_out_seconds = (
                    time_out.hour * 3600 + time_out.minute * 60 + time_out.second
                )
                # Calculate the float value from 0 to 24
                time_out_float = total_out_seconds / 3600

                self.actual_out = time_out_float

                self.remarks = iac.employee_attendance_id.name

        if import_attendance_biometrics:
            for iab in import_attendance_biometrics.filtered(
                lambda x: x.employee_attendance_id.state == "validated"
            ):
                time_in = datetime.strptime(iab.hour_from, "%H:%M:%S").time()
                # Calculate the total number of seconds since midnight
                total_in_seconds = (
                    time_in.hour * 3600 + time_in.minute * 60 + time_in.second
                )
                # Calculate the float value from 0 to 24
                time_in_float = total_in_seconds / 3600

                self.actual_in = time_in_float

                time_out = datetime.strptime(iab.hour_from, "%H:%M:%S").time()
                # Calculate the total number of seconds since midnight
                total_out_seconds = (
                    time_out.hour * 3600 + time_out.minute * 60 + time_out.second
                )
                # Calculate the float value from 0 to 24
                time_out_float = total_out_seconds / 3600

                self.actual_out = time_out_float

                self.remarks = iab.employee_attendance_id.name

        attendance_correction_obj = self.env["manual.attendance"].search(
            [
                ("name", "=", self.date),
                ("employee_id", "=", self.employee_id.id),
                ("status", "=", "validate"),
            ],
            order="create_date asc",
        )

        for att in attendance_correction_obj:
            if att.attendance_type == "out":
                self.actual_out = att.date_to
            if att.attendance_type == "in_out":
                self.actual_out = att.date_to
                if self.original != "excess":
                    self.actual_in = att.date_from

        if self.original == "excess":
            self.write({"actual_out": out_hr})

    def get_mins_for_late(self):
        """
        This function returns the Tardiness(mins) of REGULAR work schedule employees
        """
        # FOR CHECKING - Different scenarios
        mins = 0
        if self.work_schedule_type == "regular":
            if (
                self.planned_in
                and self.planned_out
                and self.actual_in
                and self.actual_out
            ):  # with attendance
                if (
                    self.actual_in > self.planned_in
                ):  # late , considered also the morning half-day absent
                    if (self.actual_in - self.planned_in) * 60 > 15:
                        mins = (self.actual_in - self.planned_in) * 60

                if "5" in self.schedule_type_ids.ids:  # absent half-day
                    mins = 0  # the deduction will be considered in undertime

                if "4" in self.schedule_type_ids.ids:  # on leave
                    if self.remarks != "Undertime":
                        mins = 0
                if "7" in self.schedule_type_ids.ids:  # holiday
                    mins = 0
                if "2" in self.schedule_type_ids.ids:  # on leave half-day
                    mins = 0  # the deduction will be considered in undertime

                if "1" in self.schedule_type_ids.ids:  # absent
                    mins = 0

        return mins

    def get_mins_for_undertime(self, work_hr, half_work_hr):
        """
        This function returns the Undertime (mins) of REGULAR work schedule employees
        """
        # FOR CHECKING - Different scenarios
        mins = 0
        vals = self.env["hr.contract"].search(
            [
                ("employee_id", "=", self.employee_id.id),
                ("state", "=", "open"),
                ("date_start", "<=", self.date),
            ],
            limit=1,
        )
        holiday_status = self.get_holiday_status(
            self.date, self.employee_id.work_location_id
        )

        if self.work_schedule_type == "regular":
            if (
                self.planned_in
                and self.planned_out
                and self.actual_in
                and self.actual_out
            ):  # with attendance

                actual_in_biased = self.actual_in
                if self.actual_in < self.planned_in:
                    actual_in_biased = self.planned_in
                actual_out_biased = self.actual_out
                if self.actual_out > self.planned_out:
                    actual_out_biased = self.planned_out

                if self.actual_out < self.planned_out:
                    mins = (self.planned_out - self.actual_out) * 60
                    if mins > 300:  # greater than 5 hours
                        mins = mins - 60

                # With leave half-day
                if "2" in self.schedule_type_ids.ids:
                    mins = (half_work_hr - (actual_out_biased - actual_in_biased)) * 60

                # With absent half-day
                if "5" in self.schedule_type_ids.ids:
                    mins = (work_hr - (actual_out_biased - actual_in_biased)) * 60

                out_diff = (self.actual_out - self.planned_out) * 60
                in_diff = (self.actual_in - self.planned_in) * 60

                # On Leave
                if "4" in self.schedule_type_ids.ids:
                    if self.remarks != "Undertime":
                        # print('undertime = 0')
                        mins = 0
                    else:
                        if in_diff <= 15:
                            if out_diff < in_diff:
                                mins = in_diff - out_diff

                if in_diff <= 15:  # grace period
                    if (
                        "5" not in self.schedule_type_ids.ids
                        and "2" not in self.schedule_type_ids.ids
                        and "4" not in self.schedule_type_ids.ids
                    ):
                        if out_diff < in_diff:
                            mins = in_diff - out_diff

                if "7" in self.schedule_type_ids.ids:  # holiday
                    # print(f"\n\n holiday")
                    if holiday_status.get("type") == "regular":
                        if not vals.daily_wage:
                            mins = 0
                        else:
                            if self.actual_time_diff < 8 and self.actual_time_diff > 0:
                                # mins = 480 - (self.actual_time_diff*60)	# Edited 05/11/23
                                mins = 0
                            elif self.actual_time_diff > 8:
                                mins = 0
                            else:
                                mins = 0
                    else:
                        mins = 0

            if mins < 0:
                mins = 0

            if self.original == "excess":
                mins = 0

        return mins

    def _get_default_requestor(self):
        return (
            self.env["hr.employee"].search([("user_id", "=", self.env.uid)], limit=1).id
        )

    def _default_employee(self):
        return self.env.context.get("default_employee_id") or self.env[
            "hr.employee"
        ].sudo().search([("user_id", "=", self.env.uid)], limit=1)

    def _ot_mail_send(
        self, employee_name, rec_name, approver, rec_id, otstage, subject_name
    ):
        url = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
        if approver == 1:
            if otstage == "pre":
                ium_name = "Pre-Overtime For Verify"
                ia_name = "Need Supervisor Pre-Approval"
            else:
                ium_name = "Pre-Overtime For Verify"
                ia_name = "Need Supervisor Pre-Approval"

            template = self.env.ref(
                "tk_payroll_overtime.email_overtime_supervisor_notification_template"
            )
            email_to = "${object.employee_id.coach_id.user_id.partner_id.email|safe}"

        else:
            if otstage == "pre":
                ium_name = "Pre-Overtime For Approval"
                ia_name = "Need Manager Pre-Approval"
            else:
                ium_name = "Pre-Overtime For Verify"
                ia_name = "Need Supervisor Pre-Approval"

            template = self.env.ref(
                "tk_payroll_overtime.email_overtime_manager_notification_template"
            )
            email_to = "${object.employee_id.parent_id.user_id.partner_id.email|safe}"

        query = """
                SELECT
                    ( SELECT ium."id" FROM ir_ui_menu ium WHERE ium."name" LIKE '%s' LIMIT 1 ) AS menu_id,
                    ( SELECT ia."id" FROM ir_act_window ia WHERE ia."name" LIKE '%s' LIMIT 1 ) AS action_id
            """ % (
            ium_name,
            ia_name,
        )
        self._cr.execute(query)
        data = self._cr.fetchall()

        t_update = """
                <![CDATA[<p></p>
                    <p>
                        Hi Mr/Ms. %s,
                        <br/>
                        <br/>
                        %s has requested your approval of the Rendered Overtime.
                        <br/>
                        Overtime Form Number: %s
                        <br/>
                        <br/>
                        You can review this request by going to the following link:
                        <br/>
                        %s/web?#id=%s&view_type=form&model=overtime.request&menu_id=%s&action=%s
                        <br/>
                        <br/>
                        Please log-in to Odoo to review this request.<br/>
                        Thank you!
                    </p>
            """ % (
            subject_name,
            employee_name,
            rec_name,
            url,
            rec_id,
            data[0][0],
            data[0][1],
        )

        template.update(
            {
                "subject": "Rendered Overtime Request",
                "body_html": t_update,
                "email_to": email_to,
            }
        )
        mail_id = (
            self.env["mail.template"]
            .browse(template.id)
            .send_mail(self.id, force_send=True)
        )

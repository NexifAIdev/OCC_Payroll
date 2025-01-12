# -*- coding: utf-8 -*-
# Native Python modules
from datetime import datetime, date, time, timedelta

# Local python modules

# Custom python modules
import pytz
from pytz import timezone

# Odoo modules
from odoo import models, fields, api, _
from odoo.tools.translate import _
from odoo.exceptions import UserError, ValidationError


class HRAttendance(models.Model):
    _inherit = "hr.attendance"

    check_in_date = fields.Date("Date", index=True, compute="_get_check_in", store=True)
    attendance_sheet_id = fields.Many2one(
        comodel_name="hr.attendance.sheet",
        string="Attendance Sheet",
        ondelete="cascade",
    )

    import_code = fields.Char(
        string="Import Code",
        copy=False,
    )
    pushed_to_sheet = fields.Boolean(
        string="Attendance Sheet Pushed",
        default=False,
        copy=False,
    )
    next_day_checkout = fields.Boolean(
        string="Next Day Checkout",
        default=False,
        copy=False,
    )

    def _occ_payroll_cfg(self):
        occ_payroll = self.env["occ.payroll.cfg"]
        return {
            "tz": (
                occ_payroll.manila_tz if occ_payroll else pytz.timezone("Asia/Manila")
            ),
        }

    def _get_check_in(self):
        for rec in self:
            rec.check_in_date = (
                fields.Datetime.context_timestamp(rec, rec.check_in)
                .astimezone(self._occ_payroll_cfg()["tz"])
                .date()
            )

    @api.model
    def _cron_update_attendance_sheet(self):
        atd_sheet_obj = self.env["hr.attendance.sheet"]
        atd_sheet = atd_sheet_obj.sudo().search(
            [("date", "=", datetime.now().strftime("%m-%d-%Y"))]
        )
        for x in atd_sheet:
            x.update_attendance_sheet()

    @api.model
    def _cron_create_attendance_sheet(self):
        atd_sheet_obj = self.env["hr.attendance.sheet"]

        # set the day of the week value
        dow_int = int(datetime.now(self._occ_payroll_cfg()["tz"]).strftime("%w")) - 1

        if dow_int == -1:
            dow_int = 6

        date_now = datetime.now(self._occ_payroll_cfg()["tz"]).strftime("%Y-%m-%d")

        # new! search for employee with active contract and returns employee_id and resource_calendar_id
        query = """
			SELECT 
				main_query.employee_id,
				(
				 CASE main_query.counter 
				 WHEN 1 THEN main_query.temp_id
				 ELSE (
								SELECT 
									resource_calendar_id 
								FROM hr_contract 
								WHERE employee_id = main_query.employee_id AND date_start::DATE <= '%s'::DATE
									AND state in ('open','pending','draft')
								ORDER BY date_start DESC 
								LIMIT 1
							)
					END
				) resource_calendar_id
			FROM 
			(
				SELECT 
					DISTINCT employee_id, count(*) as counter, sum(resource_calendar_id) as temp_id
				FROM hr_contract 
				WHERE 
					state in ('open','pending')
				GROUP BY employee_id
			) as main_query
		""" % (
            date_now
        )

        self._cr.execute(query)
        contract_ids = self._cr.dictfetchall()

        # loop creating of attendance sheet
        if contract_ids:
            for x in contract_ids:

                val = atd_sheet_obj.sudo().search(
                    [
                        ("employee_id", "=", x.get("employee_id")),
                        (
                            "date",
                            "=",
                            datetime.now(self._occ_payroll_cfg()["tz"]).strftime(
                                "%Y-%m-%d"
                            ),
                        ),
                    ]
                )

                if not val:
                    work_sched = self.get_attendance_sched(
                        date_now,
                        x.get("resource_calendar_id"),
                        self.get_attendance_sched,
                    )
                    value = {
                        "employee_id": x.get("employee_id"),
                        "date": date_now,
                        "dayofweek": str(dow_int),
                        "planned_in": work_sched.get("planned_in"),
                        "planned_out": work_sched.get("planned_out"),
                    }
                    atd_sheet_obj.create(value)

    @api.constrains("check_in", "check_out", "employee_id")
    def _check_validity(self):
        """Verifies the validity of the attendance record compared to the others from the same employee.
        For the same employee we must have :
            * maximum 1 "open" attendance record (without check_out)
            * no overlapping time slices with previous employee records
        """
        for attendance in self:
            # we take the latest attendance before our check_in time and check it doesn't overlap with ours
            last_attendance_before_check_in = self.env["hr.attendance"].search(
                [
                    ("employee_id", "=", attendance.employee_id.id),
                    ("check_in", "<=", attendance.check_in),
                    ("id", "!=", attendance.id),
                ],
                order="check_in desc",
                limit=1,
            )
            if (
                last_attendance_before_check_in
                and last_attendance_before_check_in.check_out
                and last_attendance_before_check_in.check_out > attendance.check_in
            ):
                return True
                # raise exceptions.ValidationError(_("Cannot create new attendance record for %(empl_name)s, the employee was already checked in on %(datetime)s") % {
                # 	'empl_name': attendance.employee_id.name,
                # 	'datetime': fields.Datetime.to_string(fields.Datetime.context_timestamp(self, fields.Datetime.from_string(attendance.check_in))),
                # })

            if not attendance.check_out:
                # if our attendance is "open" (no check_out), we verify there is no other "open" attendance
                no_check_out_attendances = self.env["hr.attendance"].search(
                    [
                        ("employee_id", "=", attendance.employee_id.id),
                        ("check_out", "=", False),
                        ("id", "!=", attendance.id),
                    ],
                    order="check_in desc",
                    limit=1,
                )
                if no_check_out_attendances:
                    return True
                    # raise ValidationError(_("Cannot create new attendance record for %(empl_name)s, the employee hasn't checked out since %(datetime)s") % {
                    # 	'empl_name': attendance.employee_id.name,
                    # 	'datetime': fields.Datetime.to_string(fields.Datetime.context_timestamp(self, fields.Datetime.from_string(no_check_out_attendances.check_in))),
                    # })
            else:
                # we verify that the latest attendance with check_in time before our check_out time
                # is the same as the one before our check_in time computed before, otherwise it overlaps
                last_attendance_before_check_out = self.env["hr.attendance"].search(
                    [
                        ("employee_id", "=", attendance.employee_id.id),
                        ("check_in", "<", attendance.check_out),
                        ("id", "!=", attendance.id),
                    ],
                    order="check_in desc",
                    limit=1,
                )
                if (
                    last_attendance_before_check_out
                    and last_attendance_before_check_in
                    != last_attendance_before_check_out
                ):
                    return True
                    # raise exceptions.ValidationError(_("Cannot create new attendance record for %(empl_name)s, the employee was already checked in on %(datetime)s") % {
                    # 	'empl_name': attendance.employee_id.name,
                    # 	'datetime': fields.Datetime.to_string(fields.Datetime.context_timestamp(self, fields.Datetime.from_string(last_attendance_before_check_out.check_in))),
                    # })
                    
    def _get_check_in_out_date(self, vals):
        manila_tz = timezone("Asia/Manila")
        check_in_manila = False
        check_out_manila = False
        next_day_checkout = False
        
        if vals.get("check_in", False):
            check_in = fields.Datetime.from_string(vals["check_in"]).replace(
                tzinfo=timezone("UTC")
            )
            check_in_manila = check_in.astimezone(manila_tz).replace(tzinfo=None)
            vals["check_in"] = fields.Datetime.to_string(check_in_manila)

        if vals.get("check_out", False):
            check_out = fields.Datetime.from_string(vals["check_out"]).replace(
                tzinfo=timezone("UTC")
            )
            check_out_manila = check_out.astimezone(manila_tz).replace(tzinfo=None)
            vals["check_out"] = fields.Datetime.to_string(check_out_manila)
            
        if (
            check_in_manila 
            and check_out_manila 
            and (check_out_manila > check_in_manila)
        ):
            next_day_checkout = True
            
        return {
            "vals": vals,
            "next_day_checkout": next_day_checkout
        }

    @api.model
    def create(self, vals):
        # Convert check_in and check_out to Asia/Manila timezone
        manila_tz = timezone("Asia/Manila")
        
        check_in_out_vals = self._get_check_in_out_date(vals)
        vals = check_in_out_vals.get("vals", vals)

        attendance = super(HRAttendance, self).create(vals)

        if self._context.get("check_in_date") == None:
            checkdate = (
                fields.Datetime.context_timestamp(
                    self,
                    datetime.strptime(str(str(vals["check_in"])), "%Y-%m-%d %H:%M:%S"),
                )
                .astimezone(manila_tz)
                .replace(tzinfo=None)
            )

        attendance.update({"next_day_checkout": check_in_out_vals.get("next_day_checkout", False)})

        # Automatically create a linked attendance sheet
        attendance_sheet_id = self.env["hr.attendance.sheet"].create(
            {
                "employee_id": attendance.employee_id.id,
                "date": attendance.check_in.date(),
                "actual_in": attendance.check_in.hour
                + attendance.check_in.minute / 60.0,
                "actual_out": (
                    attendance.check_out.hour + attendance.check_out.minute / 60.0
                    if attendance.check_out
                    else 0
                ),
                "attendance_id": attendance.id,
            }
        )

        attendance.attendance_sheet_id = attendance_sheet_id

        return attendance

    def write(self, vals):
        manila_tz = timezone("Asia/Manila")

        cin = vals.get("check_in", False) or datetime.strptime(
            str(self.check_in), "%Y-%m-%d %H:%M:%S"
        )
        try:
            cout = vals.get("check_out", False) or datetime.strptime(
                str(self.check_out), "%Y-%m-%d %H:%M:%S"
            )
        except:
            cout = False

        if cout:
            c_in = (
                fields.Datetime.context_timestamp(
                    self, datetime.strptime(str(str(cin)), "%Y-%m-%d %H:%M:%S")
                )
                .astimezone(manila_tz)
                .replace(tzinfo=None)
                .date()
            )
            c_out = (
                fields.Datetime.context_timestamp(
                    self, datetime.strptime(str(str(cout)), "%Y-%m-%d %H:%M:%S")
                )
                .astimezone(manila_tz)
                .replace(tzinfo=None)
                .date()
            )
            vals["next_day_checkout"] = True if c_out > c_in else False

        # Update attendance sheet on changes to check_in/check_out
        result = super(HRAttendance, self).write(vals)
        for attendance in self:
            if "check_in" in vals or "check_out" in vals:
                attendance_sheet = self.env["hr.attendance.sheet"].search(
                    [("attendance_id", "=", attendance.id)], limit=1
                )
                if attendance_sheet:
                    manila_tz = timezone("Asia/Manila")
                    if "check_in" in vals:
                        check_in = fields.Datetime.from_string(
                            vals["check_in"]
                        ).replace(tzinfo=timezone("UTC"))
                        check_in_manila = check_in.astimezone(manila_tz).replace(
                            tzinfo=None
                        )
                        attendance_sheet.actual_in = (
                            check_in_manila.hour + check_in_manila.minute / 60.0
                        )

                    if "check_out" in vals:
                        check_out = fields.Datetime.from_string(
                            vals["check_out"]
                        ).replace(tzinfo=timezone("UTC"))
                        check_out_manila = check_out.astimezone(manila_tz).replace(
                            tzinfo=None
                        )
                        attendance_sheet.actual_out = (
                            check_out_manila.hour + check_out_manila.minute / 60.0
                        )

        return result

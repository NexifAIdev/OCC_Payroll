# -*- coding: utf-8 -*-
# Native Python modules

# Local python modules

# Custom python modules

# Odoo modules
from odoo import models, fields, api, _
from odoo.tools.translate import _
from odoo.exceptions import UserError, ValidationError


class ManualAttendance(models.Model):
    _name = "manual.attendance"
    _inherit = ["mail.thread", "occ.payroll.cfg"]

    attendance_name = fields.Char(copy=False, default="New")
    status = fields.Selection(
        [
            ("draft", "Draft"),
            ("timekeeper", "Timekeeper"),
            ("manager", "Manager"),
            ("validate", "Validated"),
            ("cancel", "Cancelled"),
        ],
        copy=False,
        default="draft",
        track_visibility="onchange",
    )
    attendance_type = fields.Selection(
        [("out", "Out"), ("in_out", "In & Out")],
        string="Attendance Type",
        required=True,
        track_visibility="onchange",
    )  # ('in','In'),
    name = fields.Date(string="Date", track_visibility="onchange")
    date_from = fields.Float(string="Check In", track_visibility="onchange")
    date_to = fields.Float(string="Check Out", track_visibility="onchange")
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

    # iajw_timekeeper_ids = self.env['res.groups'].search([('name','=','Timekeeper - IAJW')]).id
    # avsc_timekeeper_ids = fields.Many2many('hr.employee', default=lambda self: self._get_timekeeper_avsc())

    # def _get_timekeeper_iajw(self):
    # 	return self.env['res.groups'].search([('name','=','Timekeeper - IAJW')]).users

    # def _get_timekeeper_avsc(self):
    # 	return self.env['res.groups'].search([('name','=','Timekeeper - AVSC')]).id

    requestor_id = fields.Many2one(
        "hr.employee",
        string="Employee Name",
        default=lambda self: self._get_default_requestor(),
        readonly=True,
    )
    # # -------EMAIL NOTIFICATIONS - START ------
    # def prep_vals(self, values):
    # 	vals = self.env.context.copy()
    # 	vals.update(values)
    # 	return vals

    # def do_email(self, temp, values):
    # 	rec = self.prep_vals(values)
    # 	template = self.env.ref(temp)
    # 	template.with_context(rec).send_mail(self.id)

    # #Manager approval (Approver 2)
    # def _get_url(self):
    # 	web_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
    # 	query = """ SELECT
    # 		(SELECT x."id" FROM ir_act_window x WHERE x."name" LIKE 'Attendance Correction' ORDER BY "id" LIMIT 1),
    # 		(SELECT ium."id" FROM ir_ui_menu ium WHERE ium."name" LIKE 'Attendances' ORDER BY "id" LIMIT 1) """
    # 	self._cr.execute(query)
    # 	data = self._cr.fetchall()

    # 	url = """ %s/web#id=%s&action=%s&model=overtime.request&view_type=form&cids=%s&menu_id=%s """ % (web_url, self.id, data[0][0], self.company_id.id, data[0][1])
    # 	return url

    # def send_email(self,approver,email_template):
    # 	url = self._get_url()
    # 	self.do_email(email_template, {'d_email': approver.email,'d_name': approver.name,'url':url})
    # # ------ EMAIL NOTIFICATIONS - END--------

    def action_submit(self):
        if self.attendance_name == "New":
            self.attendance_name = self.env["ir.sequence"].next_by_code(
                "manual_attendance_sequence"
            )
        self.status = "timekeeper"
        # approver_group = self.env['res.groups'].search([('name','=','Approver'),('category_id.name','=','Attendance Correction')],limit=1)
        # attendance_approvers=approver_group.users
        # for approver in attendance_approvers:
        # 	self.send_email(approver = approver, email_template='tk_payroll_complete.email_manual_attendance')

    def action_submit_to_manager(self):
        if self.attendance_type == "out":
            attendance_data = self.env["hr.attendance.sheet"].search(
                [("employee_id", "=", self.employee_id.id), ("date", "=", self.name)],
                limit=1,
            )
            if not attendance_data:
                raise ValidationError(
                    _("Warning! No attendance check in on this date.")
                )

        self.status = "manager"

    def action_validate(self):
        if self.env.uid != self.employee_id.parent_id.user_id.id:
            raise UserError(
                _("""Only the manager of this employee can approve the request.""")
            )
        self.status = "validate"
        if self.attendance_type == "out":
            self.write_attendance_check_out()
        elif self.attendance_type == "in_out":
            self.write_attendance_check_in_out()
        else:
            raise ValidationError(_("Warning! Not allowed to file manual attendance."))

    def reset_to_draft(self):
        self.status = "draft"

    def action_cancelled(self):
        self.status = "cancel"

    def action_cancelled_manager(self):
        self.status = "cancel"

    def write_attendance_check_out(self):
        attendance_obj = self.env["hr.attendance.sheet"]
        if self.attendance_type == "out":
            attendance_data = attendance_obj.search(
                [("employee_id", "=", self.employee_id.id), ("date", "=", self.name)],
                limit=1,
            )
            if attendance_data:
                attendance_data.write(
                    {
                        "actual_out": self.date_to,
                    }
                )
                attendance_data.update_attendance_sheet()
            else:
                raise ValidationError(
                    _("Warning! No attendance check in on this date.")
                )

    def write_attendance_check_in_out(self):
        attendance_obj = self.env["hr.attendance.sheet"]
        if self.attendance_type == "in_out":
            attendance_data = attendance_obj.search(
                [("employee_id", "=", self.employee_id.id), ("date", "=", self.name)],
                limit=1,
            )

            if not attendance_data:
                # attendance_obj.create({
                # 	'employee_id':self.employee_id.id,
                # 	'date':self.name,
                # 	'actual_in':self.date_from,
                # 	'actual_out':self.date_to,
                # })

                vals = {
                    "employee_id": self.employee_id.id,
                    "date": self.name,
                    "actual_in": self.date_from,
                    "actual_out": self.date_to,
                }
                att = attendance_obj.create(vals)

                att.update_attendance_sheet()

            else:
                attendance_data.write(
                    {"actual_in": self.date_from, "actual_out": self.date_to}
                )
                attendance_data.update_attendance_sheet()

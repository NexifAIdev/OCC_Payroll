# -*- coding: utf-8 -*-
# Native Python modules
from datetime import datetime, date, timedelta
from collections import OrderedDict
import base64, calendar, io, re
from tempfile import TemporaryFile
from pprint import pprint

# Local python modules

# Custom python modules
import xlsxwriter
from xlsxwriter.utility import xl_rowcol_to_cell
from icecream import ic

# Odoo modules
from odoo import models, fields, api, _
from odoo.tools.translate import _
from odoo.tools import float_round
from odoo.exceptions import UserError, ValidationError
import odoo.addons.decimal_precision as dp


class exhr_payroll(models.Model):
    _name = "exhr.payroll"
    _description = "Payroll Period"
    _inherit = ["mail.thread", "mail.activity.mixin", "occ.payroll.cfg"]

    company_id = fields.Many2one(
        "res.company", default=lambda self: self.env.company, required=True
    )

    name = fields.Char(
        "Payroll No.", copy=False, track_visibility="onchange", default="New"
    )
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("validated", "Validated"),
            ("posted", "Posted"),
            ("cancel", "Canceled"),
        ],
        copy=False,
        default="draft",
        track_visibility="onchange",
    )
    cutoff_date = fields.Date(string="Payout Date")
    posted_date = fields.Date()
    for_13th_mo = fields.Boolean(
        string="Non Attendance Related",
        help="For import of 13th month pay",
        default=False,
        track_visibility="onchange",
    )

    pay_period_from = fields.Date(
        string="Pay period from", index=True, track_visibility="onchange"
    )
    pay_period_to = fields.Date(
        string="Pay period to", index=True, track_visibility="onchange"
    )

    payslip_line_ids = fields.One2many("exhr.payslip", "payroll_id")

    payroll_type_id = fields.Many2one("payroll.type", string="Payroll Type")
    payment_type_id = fields.Many2one("payment.type", string="Payment Type")

    def _get_default_auto_jv(self):
        # config = self.env['payroll.accounting.config'].search([('company_id','=',self.env.company.id)])
        config = self.env["payroll.accounting.config"].search([], limit=1)
        if config:
            return config.default_auto_jv

    def _get_default_auto_post(self):
        # config = self.env['payroll.accounting.config'].search([('company_id','=',self.env.company.id)])
        config = self.env["payroll.accounting.config"].search([], limit=1)
        if config:
            return config.default_auto_post

    def _get_default_payroll_journal_id(self):
        config = self.env["payroll.accounting.config"].search(
            [("company_id", "=", self.env.company.id)]
        )
        if config:
            return config.default_payroll_journal_id.id

    def _get_default_salaries_exp_account_id(self):
        config = self.env["payroll.accounting.config"].search(
            [("company_id", "=", self.env.company.id)]
        )
        if config:
            return config.default_salaries_exp_account_id.id

    def _get_default_tax_account_id(self):
        config = self.env["payroll.accounting.config"].search(
            [("company_id", "=", self.env.company.id)]
        )
        if config:
            return config.default_tax_account_id.id

    def _get_default_sss_account_id(self):
        config = self.env["payroll.accounting.config"].search(
            [("company_id", "=", self.env.company.id)]
        )
        if config:
            return config.default_sss_account_id.id

    def _get_default_phic_account_id(self):
        config = self.env["payroll.accounting.config"].search(
            [("company_id", "=", self.env.company.id)]
        )
        if config:
            return config.default_phic_account_id.id

    def _get_default_hdmf_account_id(self):
        config = self.env["payroll.accounting.config"].search(
            [("company_id", "=", self.env.company.id)]
        )
        if config:
            return config.default_hdmf_account_id.id

    def _get_default_others_account_id(self):
        config = self.env["payroll.accounting.config"].search(
            [("company_id", "=", self.env.company.id)]
        )
        if config:
            return config.default_others_account_id.id

    def _get_default_sss_er_account_id(self):
        config = self.env["payroll.accounting.config"].search(
            [("company_id", "=", self.env.company.id)]
        )
        if config:
            return config.default_sss_er_account_id.id

    def _get_default_phic_er_account_id(self):
        config = self.env["payroll.accounting.config"].search(
            [("company_id", "=", self.env.company.id)]
        )
        if config:
            return config.default_phic_er_account_id.id

    def _get_default_hdmf_er_account_id(self):
        config = self.env["payroll.accounting.config"].search(
            [("company_id", "=", self.env.company.id)]
        )
        if config:
            return config.default_hdmf_er_account_id.id

    auto_jv = fields.Boolean(default=_get_default_auto_jv)
    auto_post = fields.Boolean(default=_get_default_auto_post)
    payroll_journal_id = fields.Many2one(
        "account.journal",
        string="Default Journal",
        default=_get_default_payroll_journal_id,
    )
    salaries_exp_account_id = fields.Many2one(
        "account.account",
        string="Salaries Expense Account",
        default=_get_default_salaries_exp_account_id,
    )
    tax_account_id = fields.Many2one(
        "account.account",
        string="Withholding Tax Account",
        default=_get_default_tax_account_id,
    )
    sss_account_id = fields.Many2one(
        "account.account",
        string="SSS Contribution Account",
        default=_get_default_sss_account_id,
    )
    phic_account_id = fields.Many2one(
        "account.account",
        string="PHIC Contribution Account",
        default=_get_default_phic_account_id,
    )
    hdmf_account_id = fields.Many2one(
        "account.account",
        string="HDMF Contribution Account",
        default=_get_default_hdmf_account_id,
    )
    others_account_id = fields.Many2one(
        "account.account",
        string="Others Account",
        default=_get_default_others_account_id,
    )
    netpay_account_id = fields.Many2one("account.account", string="Net Pay Account")
    sss_er_account_id = fields.Many2one(
        "account.account",
        string="SSS ER Contribution Account",
        default=_get_default_sss_er_account_id,
    )
    phic_er_account_id = fields.Many2one(
        "account.account",
        string="PHIC ER Contribution Account",
        default=_get_default_phic_er_account_id,
    )
    hdmf_er_account_id = fields.Many2one(
        "account.account",
        string="HDMF ER Contribution Account",
        default=_get_default_hdmf_er_account_id,
    )

    _is_thirteenth_pay = fields.Boolean(string="13th Month")

    # @api.onchange('payment_type_id')
    # def onchange_payment_type_id(self):
    # 	if self.payment_type_id:
    # 		self.netpay_account_id = self.payment_type_id.account_id

    @api.onchange("company_id")
    def onchange_company_id(self):
        if self.company_id:
            config = self.env["payroll.accounting.config"].search(
                [("company_id", "=", self.company_id.id)]
            )
            if config:
                self.auto_jv = config.default_auto_jv
                self.auto_post = config.default_auto_post
                self.payroll_journal_id = config.default_payroll_journal_id.id
                self.salaries_exp_account_id = config.default_salaries_exp_account_id.id
                self.tax_account_id = config.default_tax_account_id.id
                self.sss_account_id = config.default_sss_account_id.id
                self.phic_account_id = config.default_phic_account_id.id
                self.hdmf_account_id = config.default_hdmf_account_id.id
                self.others_account_id = config.default_others_account_id.id
                self.sss_er_account_id = config.default_sss_er_account_id.id
                self.phic_er_account_id = config.default_phic_er_account_id.id
                self.hdmf_er_account_id = config.default_hdmf_er_account_id.id

    def set_to_validated(self):

        data = self.env["exhr.payroll"].search(
            [
                ("state", "in", ["validated", "posted"]),
                ("company_id", "=", self.company_id.id),
                ("for_13th_mo", "=", False),
                ("payment_type_id", "=", self.payment_type_id.id),
                ("payroll_type_id", "=", self.payroll_type_id.id),
                ("pay_period_from", ">=", self.pay_period_from),
                ("pay_period_to", "<=", self.pay_period_to),
            ]
        )

        if not data:
            self.state = "validated"

            if self.name == "New":
                self.name = self.env["ir.sequence"].next_by_code(
                    "exhr_payroll_no_sequence"
                )

        else:
            if self.for_13th_mo == True:
                self.state = "validated"

                if self.name == "New":
                    self.name = self.env["ir.sequence"].next_by_code(
                        "exhr_payroll_no_sequence"
                    )
            else:
                primary_temp = ""
                for x in data:
                    temp = """
					- %s %s Computation range: %s to %s Status: %s""" % (
                        x.name,
                        x.payroll_type_id.name,
                        x.pay_period_from,
                        x.pay_period_to,
                        x.state,
                    )
                    primary_temp += temp

                top_temp = """Please check the computation range! It should not overlap with existing payroll record.

				The following match your payroll range and type """
                raise UserError(top_temp + primary_temp)

    def _create_account_move(self):
        move_obj = self.env["account.move"]
        move_line_obj = self.env["account.move.line"]
        # ------------TOFIX: RECODE THIS FOR AVSC---------

    def set_to_posted(self):
        for row in self.payslip_line_ids:
            if row.state == "draft":
                row.set_to_posted()

        # if self.auto_jv == True:
        # 	self._create_account_move()

        self.state = "posted"

        if not self.cutoff_date:
            self.posted_date = self.pay_period_to

        self.posted_date = fields.Date.context_today(self)

    def set_to_cancel(self):
        self.state = "cancel"

        for line in self.payslip_line_ids:
            line.set_to_cancel()

    def set_to_cancel_posted(self):
        self.state = "cancel"

        for line in self.payslip_line_ids:
            line.set_to_cancel_posted()

    def action_delete_all(self):

        self.payslip_line_ids = [(5, 0, 0)]

    def set_to_draft(self):
        self.state = "draft"

        for line in self.payslip_line_ids:
            line.set_to_draft()

    def generate_payslips_old(self):
        ic(self.payslip_line_ids)
        if not self.payslip_line_ids:
            payslip_obj = self.env["exhr.payslip"]

            query = """
			SELECT 
				DISTINCT hc.employee_id, he.employee_number
			FROM hr_contract hc
			LEFT JOIN hr_employee he ON he.id = hc.employee_id
			WHERE 
			hc.payroll_type_id = %s AND hc.payment_type_id = %s AND hc.state in ('open') AND hc.date_start <= '%s'
			AND he.active = 't' AND hc.company_id = %s AND hc.active='t'
			""" % (
                self.payroll_type_id.id,
                self.payment_type_id.id,
                self.cutoff_date,
                self.company_id.id,
            )

            self._cr.execute(query)
            data = self._cr.fetchall()

            for x in data:
                vals = {
                    "employee_id": x[0],
                    "id_number": x[1],
                    "payroll_id": self.id,
                    "pay_period_from": self.pay_period_from,
                    "pay_period_to": self.pay_period_to,
                    "cutoff_date": self.cutoff_date,
                }
                # print('employee_id : ', x[0])
                new_payslip_obj = payslip_obj.create(vals)
                new_payslip_obj.compute_payslip()
                # if new_payslip_obj:
                # 	new_payslip_obj.button_compute_payslip()

        else:
            raise UserError("Payslips are already generated.")

        # for line in self.payslip_line_ids:
        # base_salary = self.env['exhr.payslip.earnings'].search([('name_id.name','=','Base Salary'),('payslip_id','=',line.id)],limit=1).amount_subtotal
        # 	holiday_pay = self.env['exhr.payslip.earnings'].search([('name_id.name','=','Holiday Pay'),('payslip_id','=',line.id)],limit=1).amount_subtotal

        # if base_salary == 0:
        # line.unlink()

    def generate_payslips(self):
        # Reset all payslips connected to this payroll to draft status
        self.payslip_line_ids.write({"state": "draft"})
        print("All connected payslips reset to draft status.")

        # Execute query to fetch employees with active contracts matching the criteria
        query = """
            SELECT DISTINCT hc.employee_id, he.employee_number
            FROM hr_contract hc
            LEFT JOIN hr_employee he ON he.id = hc.employee_id
            WHERE 
                hc.payroll_type_id = %s AND 
                hc.payment_type_id = %s AND 
                hc.state IN ('open') AND 
                hc.date_start <= '%s' AND 
                he.active = 't' AND 
                hc.company_id = %s AND 
                hc.active = 't'
        """ % (
            self.payroll_type_id.id,
            self.payment_type_id.id,
            self.cutoff_date,
            self.company_id.id,
        )

        print(f"Executing Query:\n{query}")
        self._cr.execute(query)
        query_results = self._cr.fetchall()
        print(f"Query Results: {query_results}")

        # Convert query results into a set of tuples for easy comparison
        query_employee_set = {(row[0], row[1]) for row in query_results}
        print(f"Query Employee Set: {query_employee_set}")

        # Get current payslip lines
        current_lines = self.payslip_line_ids
        current_employee_set = {
            (line.employee_id.id, line.id_number) for line in current_lines
        }
        print(f"Current Employee Set: {current_employee_set}")

        # Determine which employees need to be added or updated
        to_add_or_update = query_employee_set - current_employee_set
        to_remove = current_employee_set - query_employee_set
        print(f"Employees to Add/Update: {to_add_or_update}")
        print(f"Employees to Remove: {to_remove}")

        # Process the records to remove
        for line in current_lines:
            if (line.employee_id.id, line.id_number) in to_remove:
                print(f"Removing payroll association for line: {line.id}")
                line.write({"payroll_id": False})  # Unlink the payroll association

        # Create or update payslip lines as needed
        payslip_obj = self.env["exhr.payslip"]
        for employee_id, id_number in to_add_or_update:
            # Search for existing record
            existing_payslip = payslip_obj.search(
                [("employee_id", "=", employee_id), ("id_number", "=", id_number)],
                limit=1,
            )

            if existing_payslip:
                print(
                    f"Updating existing payslip for Employee ID: {employee_id}, ID Number: {id_number}"
                )
                # Update the payroll_id and reset to draft
                existing_payslip.write({"payroll_id": self.id, "state": "draft"})
            else:
                print(
                    f"Creating new payslip for Employee ID: {employee_id}, ID Number: {id_number}"
                )
                # Create a new payslip record
                vals = {
                    "employee_id": employee_id,
                    "id_number": id_number,
                    "payroll_id": self.id,
                    "pay_period_from": self.pay_period_from,
                    "pay_period_to": self.pay_period_to,
                    "cutoff_date": self.cutoff_date,
                }
                new_payslip_obj = payslip_obj.create(vals)
                print(f"New Payslip Created: {new_payslip_obj.id}")
                new_payslip_obj.payroll_id = self.id
                new_payslip_obj.state = "draft"
                new_payslip_obj.compute_payslip()

        print("Payslip generation completed.")

    # - - - - - - PRINT PAYROLL SLIP - - - - - - - - -

    excel_file = fields.Binary("Excel File")

    def print_payroll_sheet(self):
        output = io.BytesIO()
        row = 0
        col = 0
        workbook = xlsxwriter.Workbook(output)

        # FORMATTING
        headerformat = workbook.add_format(
            {
                "bold": 1,
                "border": 1,
                "bottom": 1,
                "align": "center",
                "valign": "vcenter",
                "text_wrap": True,
                "font_size": 10,
                "bg_color": "#F4F0F0",
            }
        )
        moneyformat = workbook.add_format(
            {
                "align": "center",
                "valign": "vcenter",
                "font_size": 10,
                "num_format": "#,##0.00",
            }
        )
        titleformat = workbook.add_format(
            {"bold": 1, "align": "left", "valign": "vcenter", "font_size": 12}
        )
        centerformat = workbook.add_format(
            {"align": "center", "valign": "vcenter", "font_size": 10}
        )
        leftformat = workbook.add_format(
            {"align": "left", "valign": "vcenter", "font_size": 10}
        )
        rateformat = workbook.add_format(
            {"align": "left", "valign": "vcenter", "color": "blue", "font_size": 10}
        )
        amount_format = workbook.add_format(
            {
                "align": "left",
                "valign": "vcenter",
                "font_size": 10,
                "num_format": "#,##0.00",
            }
        )
        amount_rate_format = workbook.add_format(
            {
                "align": "left",
                "valign": "vcenter",
                "color": "blue",
                "font_size": 10,
                "num_format": "#,##0.00",
            }
        )

        worksheet = workbook.add_worksheet("Payroll Sheet")
        worksheet.freeze_panes(5, 3)
        worksheet.set_column("A:A", 5)  # Count
        worksheet.set_column("B:B", 5)  # Emp ID??
        worksheet.set_column("C:C", 30)  # Emp Name
        worksheet.set_column("D:D", 15)
        worksheet.set_column("E:E", 4)
        worksheet.set_column("H:H", 4)
        worksheet.set_column("K:K", 4)
        worksheet.merge_range(0, 0, 0, 2, "Formalum Industries", titleformat)
        worksheet.merge_range(
            1, 0, 1, 2, "Payment for the period covered:", titleformat
        )
        worksheet.merge_range(3, 0, 3, 2, "Name", titleformat)
        worksheet.write(3, 3, "Daily Rate", titleformat)
        worksheet.merge_range(3, 4, 3, 5, "Basic Pay", titleformat)
        worksheet.write(3, 6, "OT Rate", titleformat)
        worksheet.merge_range(3, 7, 3, 8, "Overtime", titleformat)
        worksheet.merge_range(3, 9, 3, 11, "Sunday", titleformat)
        worksheet.merge_range(3, 12, 3, 13, "Regular Holiday", titleformat)
        worksheet.merge_range(3, 14, 3, 15, "Special Holiday", titleformat)
        worksheet.merge_range(3, 16, 3, 18, "Night Diff", titleformat)
        worksheet.write(3, 19, "COLA", titleformat)
        worksheet.write(3, 20, "Leaves", titleformat)
        worksheet.write(3, 21, "Adjustments", titleformat)
        worksheet.write(3, 22, "Rate", titleformat)
        worksheet.merge_range(3, 23, 3, 24, "Late/Undertime", titleformat)
        worksheet.write(3, 25, "Gross Pay", titleformat)
        worksheet.write(3, 26, "HDMF Contribution", titleformat)
        worksheet.write(3, 27, "HDMF Calamity Loan", titleformat)
        worksheet.write(3, 28, "HDMF Salary Loan", titleformat)
        worksheet.write(3, 29, "SSS Loan", titleformat)
        worksheet.write(3, 30, "SSS Calamity Loan", titleformat)
        worksheet.write(3, 31, "SSS Salary Loan", titleformat)
        worksheet.write(3, 32, "Philhealth Contribution", titleformat)
        worksheet.write(3, 33, "Other Deductions", titleformat)
        worksheet.write(3, 34, "Net Pay", titleformat)

        worksheet.write(4, 1, "ID", amount_format)
        worksheet.write(4, 2, "Name", amount_format)
        worksheet.write(4, 4, "Days", amount_format)
        worksheet.write(4, 5, "Amount", amount_format)
        worksheet.write(4, 7, "Hrs", amount_format)
        worksheet.write(4, 7, "Amount", amount_format)
        worksheet.write(4, 9, "Rest Day Rate", amount_format)
        worksheet.write(4, 10, "Days", amount_format)
        worksheet.write(4, 11, "Amount", amount_format)
        worksheet.write(4, 12, "Days", amount_format)
        worksheet.write(4, 12, "Amount", amount_format)
        # worksheet.write_formula('R6', "=SUM(D6:P6)")

        row = 5
        dept = ""
        count = 1
        emp = ""

        for emp in self.payslip_line_ids:
            cr = row + 1
            rh_d = 0
            sh_d = 0
            dh_d = 0
            rd_hr = 0
            hr_rate = 0
            ot_rate = 0

            # POINTS
            ot_hr = 0
            rh_w_hr = 0
            sh_w_hr = 0
            dh_w_hr = 0
            rd_w_hr = 0
            nd_ot_hr = 0

            hdr_qry = """
					SELECT 
						dept.name,
						em.name,
						hc.wage as monthly_wage,
						hc.hourly_rate,
						hc.daily_rate

						From hr_employee em 
						LEFT JOIN hr_contract hc ON hc.employee_id = em.id AND hc.state NOT IN ('close','cancel')
						LEFT JOIN hr_department dept ON dept.id = em.department_id
						WHERE em.id = %s
						""" % (
                emp.employee_id.id
            )

            self._cr.execute(hdr_qry)
            contract = self._cr.fetchall()

            worksheet.write(row, col + 0, count, leftformat)  # Employee
            worksheet.write(row, col + 1, emp.employee_id.name, leftformat)  # Employee
            worksheet.write(
                row, col + 2, emp.employee_id.employee_number, leftformat
            )  # Employee Number
            count += 1
            for cn in contract:
                hr_rate = int(cn[3])
                # ================ R A T E S ======================
                # Daily Rate
                worksheet.write(row, col + 3, cn[4], amount_rate_format)
                attendance = self.env["hr.attendance.sheet"].search(
                    [
                        ("employee_id", "=", emp.employee_id.id),
                        ("schedule_type_ids", "=", False),
                        ("planned_in", ">", 0),
                        ("planned_out", ">", 0),
                        ("date", ">=", self.pay_period_from),
                        ("date", "<=", self.pay_period_to),
                    ]
                )

                # Attendance
                worksheet.write(row, col + 4, len(attendance), amount_format)
                worksheet.write_formula(
                    "F" + str(cr), "=E" + str(cr) + "*D" + str(cr), amount_format
                )
                # worksheet.write(row, col+5, len(attendance) * cn[4], amount_format)#Basic Pay

                # OT Rate
                ot_rate = (
                    self.env["overtime.rate.config"]
                    .search([("rate_id", "=", 16)])
                    .percentage
                )
                worksheet.write_formula(
                    "G" + str(cr),
                    "=(D" + str(cr) + "/8)*" + str(ot_rate),
                    amount_rate_format,
                )
                worksheet.write_formula(
                    "I" + str(cr), "=G" + str(cr) + "*H" + str(cr), amount_format
                )
                # worksheet.write(row, col+6, cn[3]*ot_rate , amount_rate_format)

                # Rest Day Rate
                rd_ot_rate = (
                    self.env["overtime.rate.config"]
                    .search([("rate_id", "=", 1)])
                    .percentage
                )
                worksheet.write_formula(
                    "J" + str(cr),
                    "=D" + str(cr) + "*" + str(rd_ot_rate),
                    amount_rate_format,
                )
                worksheet.write_formula(
                    "L" + str(cr), "=J" + str(cr) + "*K" + str(cr), amount_format
                )

                # worksheet.write(row, col+9, cn[4]*rd_ot_rate , amount_rate_format)#OT Rate

                # Ordinary Day (1)
                od_ot_rate = (
                    self.env["overtime.rate.config"]
                    .search([("rate_id", "=", 0)])
                    .percentage
                )

                # Night Diff Rate
                nd_ot_rate = (
                    self.env["overtime.rate.config"]
                    .search([("rate_id", "=", 8)])
                    .percentage
                )
                worksheet.write_formula(
                    "Q" + str(cr),
                    "=(D" + str(cr) + "/8)*" + str(nd_ot_rate - od_ot_rate),
                    amount_rate_format,
                )
                worksheet.write_formula(
                    "S" + str(cr), "=Q" + str(cr) + "*R" + str(cr), amount_format
                )

                # worksheet.write(row, col+9, cn[4]*rd_ot_rate , amount_rate_format)#OT Rate

                # Regular Holiday
                rh_rate = (
                    self.env["overtime.rate.config"]
                    .search([("rate_id", "=", 4)])
                    .percentage
                )
                worksheet.write_formula(
                    "N" + str(cr), "=M" + str(cr) + "*D" + str(cr), amount_rate_format
                )

                # Special Holiday
                sh_rate = (
                    self.env["overtime.rate.config"]
                    .search([("rate_id", "=", 2)])
                    .percentage
                )
                worksheet.write_formula(
                    "P" + str(cr),
                    "=D" + str(cr) + "*" + str(sh_rate) + "*O" + str(cr),
                    amount_rate_format,
                )

                # Gross Pay
                worksheet.write_formula(
                    "Z" + str(cr),
                    "=F"
                    + str(cr)
                    + "+I"
                    + str(cr)
                    + "+L"
                    + str(cr)
                    + "+N"
                    + str(cr)
                    + "+P"
                    + str(cr)
                    + "+S"
                    + str(cr)
                    + "+T"
                    + str(cr)
                    + "+U"
                    + str(cr)
                    + "+V"
                    + str(cr)
                    + "-Y"
                    + str(cr),
                    amount_rate_format,
                )

            # ======================= A T T E N D A N C E ===================
            attendance = self.env["hr.attendance.sheet"].search(
                [
                    ("employee_id", "=", emp.employee_id.id),
                    ("date", ">=", self.pay_period_from),
                    ("date", "<=", self.pay_period_to),
                ]
            )
            for att in attendance:
                # Regular Holiday
                if att.rate_type in ("4", "5", "12", "13", "20", "21", "28", "29"):
                    rh_d += 1

                # Special Holiday
                elif att.rate_type in ("2", "3", "10", "11", "18", "19", "26", "27"):
                    sh_d += 1

                # Double Holiday
                elif att.rate_type in ("6", "7", "14", "15", "22", "23", "30", "31"):
                    dh_d += 1

                # Rest Day
                elif att.rate_type in (
                    "1",
                    "3",
                    "5",
                    "7",
                    "9",
                    "11",
                    "13",
                    "15",
                    "17",
                    "19",
                    "21",
                    "23",
                    "25",
                    "27",
                    "29",
                    "31",
                ):
                    # Non-Ot or sheduled sunday work time
                    if att.planned_in > 0 and att.actual_in > 0:
                        print(
                            'this is not an "overtime" however sundays are always rated as Rest Day Rate (1.3)'
                        )
                        print(
                            "took from attendance since this is the employees schedule, OT logging is not necessary"
                        )
                        rendered_hr = att.actual_out - att.actual_in
                        rd_hr += rendered_hr

            ot_qry = """
					SELECT 
						total_ot_hrs AS overtime, -- 0
						otl.rate_type, -- 1
						otl.actual_in, -- 2
						otl.actual_out, -- 3
						CASE TO_CHAR(otl.date + INTERVAL '8 HOUR', 'D') WHEN '1' THEN 6 WHEN '2' THEN 0 WHEN '3' THEN 1 WHEN '4' THEN 2 WHEN '5' THEN 3 WHEN '6' THEN 4 WHEN '7' THEN 5 END AS dayofweek,  -- 4
						( SELECT COUNT(i) FROM generate_series(TO_CHAR(otl.date, 'YYYY-MM-01')::DATE, (TO_CHAR(otl.date, 'YYYY-MM-01')::DATE + INTERVAL '1 MONTH' - INTERVAL '1 DAY')::DATE, INTERVAL '1 DAY') AS i WHERE to_char(i::date, 'DY') NOT IN ('SAT','SUN') ) daysofmonth,  -- 5
						conf.percentage AS overtime_percentage, -- 6
						conf.name, -- 7
						
						has.planned_in, -- 8
						has.planned_out -- 9
					FROM overtime_request_line otl
					LEFT JOIN overtime_request otr ON otl.overtime_id = otr.id
					LEFT JOIN overtime_rate_config conf ON conf.rate_id = otl.rate_type::INTEGER 
					LEFT JOIN hr_attendance_sheet has ON has.date = otl.date and has.employee_id = otl.employee_id
					WHERE otl.date BETWEEN '%s'::DATE AND '%s'::DATE
					AND otl.status != 'paid'
					AND otr.employee_id = %s
					AND otr.state = 'approved'""" % (
                self.pay_period_from,
                self.pay_period_to,
                emp.employee_id.id,
            )

            self._cr.execute(ot_qry)
            ots = self._cr.fetchall()
            for ot in ots:
                # # Rest Day, 1.3
                if ot[1] in (
                    "1",
                    "3",
                    "5",
                    "7",
                    "9",
                    "11",
                    "13",
                    "15",
                    "17",
                    "19",
                    "21",
                    "23",
                    "25",
                    "27",
                    "29",
                    "31",
                ):
                    rd_w_hr += int(ot[0])

                # regular holiday, percent/2.00
                if ot[1] in ("4", "5", "12", "13", "20", "21", "28", "29"):
                    rh_w_hr += int(ot[0])

                # special day, percent/1.3
                if ot[1] in ("3", "10", "11", "18", "19", "26", "27"):
                    sh_w_hr += int(ot[0])

                # double day, percent/3
                if ot[1] in ("3", "10", "11", "18", "19", "26", "27"):
                    dh_w_hr += ot[0]

                ot_st = int(ot[2])
                ot_end = int(ot[3])
                plan_in = int(ot[8])
                plan_out = int(ot[9])
                # This is overtime 1.3
                if int(ot[1]) in (
                    16,
                    17,
                    18,
                    19,
                    20,
                    21,
                    22,
                    23,
                    24,
                    25,
                    26,
                    27,
                    28,
                    29,
                    30,
                    31,
                ):
                    # Ordinary Day OT
                    if int(ot[1]) in (16, 24):
                        ot_hr += int(ot[0])

                    # Special Day Scenarios
                    if int(ot[1]) not in (16, 24):
                        # more than whole day, started earlier, and ended earlier than work sched
                        # ot_st < pl_start and ot_end > pl_out
                        if ot_st < plan_in and ot_end > plan_out:
                            ot_hr += plan_in - ot_st
                            ot_hr += ot_end - plan_out

                        # started earlier than schedule
                        elif ot_st < plan_in and ot_end < plan_out:
                            # ot before start of time schedule
                            if ot_end < plan_in:
                                ot_hr += ot_end - ot_st

                            # ot just started early and ended within time schedule
                            elif ot_end > plan_in:
                                ot_hr += plan_in - ot_st

                        # ended later than schedule
                        elif ot_end > plan_out and ot_st > plan_in:
                            if ot_st > plan_out:
                                ot_hr += ot_end - ot_st
                            elif ot_st > plan_out:
                                ot_hr += ot_st - plan_out

                    # nd_ot_hr =self.env['exhr.payslip.earnings'].search([('payslip_id','=',emp.id),('name_id','=',3)]).no_day_hrs
                    # night_diff, 1.1
                    if int(ot[1]) in (
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
                        # 	# strip off non night
                        nd_start = (
                            self.env["hr.attendance.sheet"]
                            .search(
                                [
                                    ("employee_id", "=", emp.employee_id.id),
                                    ("date", ">=", self.pay_period_from),
                                    ("date", "<=", self.pay_period_to),
                                ],
                                limit=1,
                            )
                            .ns_start
                        )
                        nd_end = (
                            self.env["hr.attendance.sheet"]
                            .search(
                                [
                                    ("employee_id", "=", emp.employee_id.id),
                                    ("date", ">=", self.pay_period_from),
                                    ("date", "<=", self.pay_period_to),
                                ],
                                limit=1,
                            )
                            .ns_end
                        )

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

            # Ordinary Day OT
            worksheet.write(row, col + 7, ot_hr, amount_format)  # OT Hr Count

            # Rest Day OT - ot_rd are approved OTs; rd_hr are scheduled attendance
            worksheet.write(row, col + 10, rd_w_hr / 8, amount_format)  # OT Hr Count

            # Regular Holiday OT - ot_rd are approved OTs; rd_hr are scheduled attendance
            worksheet.write(row, col + 12, rh_d, amount_format)  # OT Amount

            # Special Holiday
            worksheet.write(row, col + 14, sh_d, amount_format)  # OT Amount

            # Night Differential
            worksheet.write(row, col + 17, nd_ot_hr, amount_format)  # OT Amount

            cola_qry = """
				SELECT sum(amount_total) from exhr_payslip_nontaxable
				Left join nontaxable_type tp ON tp.id = name_id
				where tp.name='COLA' and payslip_id = %s """ % (
                emp.id
            )
            self._cr.execute(cola_qry)
            cola = self._cr.fetchall()
            for cl in cola:
                worksheet.write(row, col + 19, cl[0], amount_format)  # OT Amount

            #
            row += 1

        worksheet.set_column("G:K", None, None, {"hidden": True})
        workbook.close()
        output.seek(0)
        xy = output.read()
        self.write({"excel_file": base64.encodestring(xy)})

        return {
            "type": "ir.actions.act_url",
            "url": "/web/content/exhr.payroll/%s/excel_file/Payroll Sheet.xlsx?download=true"
            % (self.id),
        }

    # - - - - - END - PRINT PAYROLL SLIP - - - - - -

    def get_ot_rate(self, rate_type, hourly_rate, isHoliday):
        percent = (
            self.env["overtime.rate.config"]
            .search([("rate_id", "=", rate_type)])
            .percentage
        )

        return percent * hourly_rate

    def generate_thirteenth(self):
        ic("generate_thirteenth")
        ic(self.payslip_line_ids)
        if not self.payslip_line_ids:
            payslip_obj = self.env["exhr.payslip"]
            nontax_type_id = self.env["nontaxable.type"].search(
                [("name", "=", "Earned 13th Month"), ("active", "=", True)]
            )
            company_id = self.company_id

            employee_query = """
				SELECT DISTINCT
					he.name,
					rc.name,
					he.id

				FROM exhr_payslip ep
				LEFT JOIN hr_employee he ON he.id = ep.employee_id
				LEFT JOIN res_company rc ON rc.id = ep.company_id

				WHERE ep.pay_period_from >= '%s'
				and ep.pay_period_to <= '%s'
				and ep.state = 'posted' AND rc.id = %s

				ORDER BY he.name ASC
			""" % (
                self.pay_period_from,
                self.pay_period_to,
                self.company_id.id,
            )

            employee = ""
            emp_id = 0

            self._cr.execute(employee_query)
            data = self._cr.fetchall()
            print(employee_query)
            ic(data)

            for person in data:
                if person[0] != employee:
                    employee = person[0]
                    emp_id = person[2]

                    earnings_query = """
					SELECT
						he.name,
						(CASE WHEN et.name='Base Salary' THEN tpe.amount_subtotal ELSE 0 END) as base_salary,
						(CASE WHEN et.name='Leave Pay' THEN tpe.amount_subtotal ELSE 0 END) as leave_pay,
						(CASE WHEN et.name='Holiday Pay' THEN tpe.amount_subtotal ELSE 0 END) as holi_pay,
						(CASE WHEN et.name='Adjustment: Salary' THEN tpe.amount_subtotal ELSE 0 END) as adj_salary,
						tp.cutoff_date

					FROM exhr_payslip ep
					LEFT JOIN hr_employee he ON he.id=ep.employee_id
					LEFT JOIN exhr_payslip_earnings epe ON epe.payslip_id = ep.id
					LEFT JOIN earnings_type et ON et.id = epe.name_id
					LEFT JOIN res_company rc ON rc.id = ep.company_id

					WHERE ep.pay_period_from >= '%s'
					and ep.pay_period_to <= '%s'
					and ep.state = 'posted'
					and rc.id = %s
					and he.id = %s

					ORDER BY he.name, tp.cutoff_date
					""" % (
                        self.pay_period_from,
                        self.pay_period_to,
                        self.company_id.id,
                        emp_id,
                    )

                    self._cr.execute(earnings_query)
                    earnings = self._cr.fetchall()
                    
                    print(earnings_query)
                    ic(earnings)

                    base_salary = 0
                    leave_pay = 0
                    holi_pay = 0
                    adj_salary = 0
                    tot_basic_pay = 0

                    for earn in earnings:
                        base_salary += earn[1]
                        leave_pay += earn[2]
                        holi_pay += earn[3]
                        adj_salary += earn[4]

                    journal_account = ""
                    analytic_account_id = ""
                    analytic_tag_ids = ""
                    journal_account2 = ""
                    analytic_account_id2 = ""
                    analytic_tag_ids2 = ""

                    jv_employee = self.env["hr.employee"].search(
                        [("id", "=", emp_id)], limit=1
                    )
                    journal_account = (
                        jv_employee.accounting_tag_id.default_13th_month_account_id
                    )
                    journal_payable = (
                        jv_employee.accounting_tag_id.default_13th_payable_account_id.name
                    )
                    analytic_account_id = jv_employee.analytic_account_id.name
                    analytic_tag_ids = jv_employee.analytic_account_id.analytic_tag_ids
                    analytic_list = []
                    for j in analytic_tag_ids:
                        analytic_list.append(j.name)

                    if not journal_account:
                        jv_employee2 = self.env["hr.employee"].search(
                            [("id", "=", emp_id), ("active", "=", False)], limit=1
                        )
                        journal_account2 = (
                            jv_employee2.accounting_tag_id.default_13th_month_account_id
                        )
                        journal_payable2 = (
                            jv_employee2.accounting_tag_id.default_13th_payable_account_id.name
                        )
                        analytic_account_id2 = jv_employee2.analytic_account_id.name
                        analytic_tag_ids2 = (
                            jv_employee2.analytic_account_id.analytic_tag_ids
                        )
                        analytic_list2 = []
                        for k in analytic_tag_ids2:
                            analytic_list2.append(k.name)

                    # total basic pay
                    tot_basic_pay = base_salary + leave_pay + holi_pay + adj_salary

                    ded_query = """
					SELECT
						he.name,
						(CASE WHEN dt.name='Tardiness' THEN epd.amount_total ELSE 0 END) as tardy_ded,
						(CASE WHEN dt.name='Undertime' THEN epd.amount_total ELSE 0 END) as under_ded,
						(CASE WHEN dt.name='Leave w/o pay' THEN epd.amount_total ELSE 0 END) as lwop_ded,
						ep.cutoff_date

					FROM exhr_payslip ep
					LEFT JOIN hr_employee he ON he.id=ep.employee_id
					LEFT JOIN exhr_payslip_deductions epd ON epd.payslip_id = ep.id
					LEFT JOIN deduction_type dt ON dt.id = epd.name_id
					LEFT JOIN res_company rc ON rc.id = ep.company_id

					WHERE ep.pay_period_from >= '%s'
					and ep.pay_period_to <= '%s'
					and ep.state = 'posted'
					and rc.id = %s
					and he.id = %s

					ORDER BY he.name, ep.cutoff_date
					""" % (
                        self.pay_period_from,
                        self.pay_period_to,
                        self.company_id.id,
                        emp_id,
                    )

                    self._cr.execute(ded_query)
                    deduction = self._cr.fetchall()
                    
                    print(ded_query)
                    ic(deduction)

                    tardy_ded = 0
                    under_ded = 0
                    lwop_ded = 0
                    tot_deduction = 0
                    net_basic_pay = 0
                    pay_computation = 0

                    for ded in deduction:
                        tardy_ded += ded[1]
                        under_ded += ded[2]
                        lwop_ded += ded[3]

                    # total deduction
                    tot_deduction = tardy_ded + under_ded + lwop_ded

                    # total 13th month
                    net_basic_pay = tot_basic_pay - tot_deduction
                    pay_computation = net_basic_pay / 12

                    analytic_string = ",".join(map(str, analytic_list))

                    if not analytic_account_id:
                        analytic_string2 = ",".join(map(str, analytic_list2))

                    vals = {
                        "employee_id": emp_id,
                        "id_number": jv_employee.employee_number,
                        "payroll_id": self.id,
                        "pay_period_from": self.pay_period_from,
                        "pay_period_to": self.pay_period_to,
                        "cutoff_date": self.cutoff_date,
                        "company_id": company_id.id,
                    }
                    new_payslip_obj = payslip_obj.create(vals)

                    nontax_obj = self.env["exhr.payslip.nontaxable"]
                    new_nontax_obj = nontax_obj.create(
                        {
                            "pay_type": "earnings",
                            "payslip_id": new_payslip_obj.id,
                            "name_id": nontax_type_id.id,
                            "ref": "Earned 13th month for %s - %s"
                            % (self.pay_period_from, self.pay_period_to),
                            "amount_total": pay_computation,
                            "gl_account_id": journal_account.id or journal_account2.id,
                        }
                    )
                    new_nontax_obj.onchange_amount_total()

        else:
            raise UserError("Payslips are already generated.")

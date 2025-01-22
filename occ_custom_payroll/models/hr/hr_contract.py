# -*- coding: utf-8 -*-
# Native Python modules

# Local python modules

# Custom python modules

# Odoo modules
from odoo import models, fields, api, _
from odoo.tools.translate import _
from odoo.exceptions import UserError, ValidationError


class HrContract(models.Model):
    _inherit = "hr.contract"

    text_formula = """
	<p>&nbsp;Estimated Equivalent Monthly Rate&nbsp;</p>
	<table style="border-collapse: collapse; width: 87%; margin-left: calc(13%);" width="376" cellspacing="0" cellpadding="0" border="0">
	  <tbody>
		<tr>
		  <td class="xl65" style="color: black; font-size: 16px; font-weight: 400; font-style: normal; text-decoration: none; font-family: Calibri, sans-serif; text-align: center; vertical-align: bottom; border-image: none 100% / 1 / 0 stretch; border-color: currentcolor currentcolor windowtext; border-style: none none solid; border-width: medium medium 0.5pt; height: 16pt; width: 38.7395%;" width="76.86170212765957%" height="21"><span style="font-family: &quot;Times New Roman&quot;, Times, serif; font-size: 14px;">Applicable Daily Rate (ADR)</span><span style="font-size: 14px;"><span style="font-family: Arial,Helvetica,sans-serif;">&nbsp;x&nbsp;</span></span><span style="color: rgb(68, 114, 196); font-size: 14px; font-weight: 400; font-style: normal; text-decoration: none; font-family: Arial, Helvetica, sans-serif;">Days</span></td>
		  <td class="xl64" rowspan="2" style="color: black; font-size: 16px; font-weight: 400; font-style: normal; text-decoration: none; font-family: Calibri, sans-serif; text-align: center; vertical-align: middle; border: medium none; width: 61.0924%;" width="15.138297872340427%">
			<div style="text-align: left;">&nbsp;= <span style="font-family: 'Times New Roman',Times,serif;">EEMR</span></div>
		  </td>
		</tr>
		<tr>
		  <td class="xl66" style="color: rgb(68, 114, 196); font-size: 16px; font-weight: 400; font-style: normal; text-decoration: none; font-family: &quot;Calibri (Body)&quot;; text-align: center; vertical-align: bottom; border: medium none; height: 16pt; width: 38.7395%;" height="21"><span style="font-size: 14px; font-family: Arial, Helvetica, sans-serif;">Months</span></td>
		</tr>
	  </tbody>
	</table>
	"""
    # EEMR Computation
    eemr_hours = fields.Float("Hours", default=8)
    eemr_days = fields.Float("Days", default=313)
    eemr_months = fields.Float("Month", default=12)
    payment_type = fields.Selection(
        [("monthly", "Monthly"), ("daily", "Daily")],
        string="Payment Type",
        default="monthly",
    )
    html_formula = fields.Html(default=text_formula)

    # SSS Contribution
    sss_1st_co_date = fields.Selection(
        [
            ("1", "1st"),
            ("2", "2nd"),
            ("3", "3rd"),
            ("4", "4th"),
            ("5", "5th"),
            ("6", "6th"),
            ("7", "7th"),
            ("8", "8th"),
            ("9", "9th"),
            ("10", "10th"),
            ("11", "11th"),
            ("12", "12th"),
            ("13", "13th"),
            ("14", "14th"),
            ("15", "15th"),
            ("16", "16th"),
            ("17", "17th"),
            ("18", "18th"),
            ("19", "19th"),
            ("20", "20th"),
            ("21", "21th"),
            ("22", "22th"),
            ("23", "23th"),
            ("24", "24th"),
            ("25", "25th"),
            ("26", "26th"),
            ("27", "27th"),
            ("28", "28th"),
            ("29", "29th"),
            ("30", "30th"),
        ],
        help="SSS Contribution 1st cut-off day.",
        default="1",
    )
    sss_2nd_co_date = fields.Selection(
        [
            ("1", "1st"),
            ("2", "2nd"),
            ("3", "3rd"),
            ("4", "4th"),
            ("5", "5th"),
            ("6", "6th"),
            ("7", "7th"),
            ("8", "8th"),
            ("9", "9th"),
            ("10", "10th"),
            ("11", "11th"),
            ("12", "12th"),
            ("13", "13th"),
            ("14", "14th"),
            ("15", "15th"),
            ("16", "16th"),
            ("17", "17th"),
            ("18", "18th"),
            ("19", "19th"),
            ("20", "20th"),
            ("21", "21th"),
            ("22", "22th"),
            ("23", "23th"),
            ("24", "24th"),
            ("25", "25th"),
            ("26", "26th"),
            ("27", "27th"),
            ("28", "28th"),
            ("29", "29th"),
            ("30", "30th"),
        ],
        help="SSS Contribution 2nd cut-off day.",
        default="16",
    )

    # PHIC Contribution
    phic_1st_co_date = fields.Selection(
        [
            ("1", "1st"),
            ("2", "2nd"),
            ("3", "3rd"),
            ("4", "4th"),
            ("5", "5th"),
            ("6", "6th"),
            ("7", "7th"),
            ("8", "8th"),
            ("9", "9th"),
            ("10", "10th"),
            ("11", "11th"),
            ("12", "12th"),
            ("13", "13th"),
            ("14", "14th"),
            ("15", "15th"),
            ("16", "16th"),
            ("17", "17th"),
            ("18", "18th"),
            ("19", "19th"),
            ("20", "20th"),
            ("21", "21th"),
            ("22", "22th"),
            ("23", "23th"),
            ("24", "24th"),
            ("25", "25th"),
            ("26", "26th"),
            ("27", "27th"),
            ("28", "28th"),
            ("29", "29th"),
            ("30", "30th"),
        ],
        help="PHIC Contribution 1st cut-off day.",
        default="1",
    )
    phic_2nd_co_date = fields.Selection(
        [
            ("1", "1st"),
            ("2", "2nd"),
            ("3", "3rd"),
            ("4", "4th"),
            ("5", "5th"),
            ("6", "6th"),
            ("7", "7th"),
            ("8", "8th"),
            ("9", "9th"),
            ("10", "10th"),
            ("11", "11th"),
            ("12", "12th"),
            ("13", "13th"),
            ("14", "14th"),
            ("15", "15th"),
            ("16", "16th"),
            ("17", "17th"),
            ("18", "18th"),
            ("19", "19th"),
            ("20", "20th"),
            ("21", "21th"),
            ("22", "22th"),
            ("23", "23th"),
            ("24", "24th"),
            ("25", "25th"),
            ("26", "26th"),
            ("27", "27th"),
            ("28", "28th"),
            ("29", "29th"),
            ("30", "30th"),
        ],
        help="PHIC Contribution 2nd cut-off day.",
        default="16",
    )

    # HDMF Contribution
    hdmf_1st_co_date = fields.Selection(
        [
            ("1", "1st"),
            ("2", "2nd"),
            ("3", "3rd"),
            ("4", "4th"),
            ("5", "5th"),
            ("6", "6th"),
            ("7", "7th"),
            ("8", "8th"),
            ("9", "9th"),
            ("10", "10th"),
            ("11", "11th"),
            ("12", "12th"),
            ("13", "13th"),
            ("14", "14th"),
            ("15", "15th"),
            ("16", "16th"),
            ("17", "17th"),
            ("18", "18th"),
            ("19", "19th"),
            ("20", "20th"),
            ("21", "21th"),
            ("22", "22th"),
            ("23", "23th"),
            ("24", "24th"),
            ("25", "25th"),
            ("26", "26th"),
            ("27", "27th"),
            ("28", "28th"),
            ("29", "29th"),
            ("30", "30th"),
        ],
        help="HDMF Contribution 1st cut-off day.",
        default="1",
    )
    hdmf_2nd_co_date = fields.Selection(
        [
            ("1", "1st"),
            ("2", "2nd"),
            ("3", "3rd"),
            ("4", "4th"),
            ("5", "5th"),
            ("6", "6th"),
            ("7", "7th"),
            ("8", "8th"),
            ("9", "9th"),
            ("10", "10th"),
            ("11", "11th"),
            ("12", "12th"),
            ("13", "13th"),
            ("14", "14th"),
            ("15", "15th"),
            ("16", "16th"),
            ("17", "17th"),
            ("18", "18th"),
            ("19", "19th"),
            ("20", "20th"),
            ("21", "21th"),
            ("22", "22th"),
            ("23", "23th"),
            ("24", "24th"),
            ("25", "25th"),
            ("26", "26th"),
            ("27", "27th"),
            ("28", "28th"),
            ("29", "29th"),
            ("30", "30th"),
        ],
        help="HDMF Contribution 2nd cut-off day.",
        default="16",
    )

    # rename wage to Basic salary
    wage = fields.Monetary(
        "Base Salary",
        digits=(16, 2),
        required=True,
        track_visibility="onchange",
        help="Employee's monthly gross wage.",
    )

    payroll_type_id = fields.Many2one(
        "payroll.type", string="Payroll Type", track_visibility="onchange"
    )
    payment_type_id = fields.Many2one(
        "payment.type", string="Payment Type", track_visibility="onchange"
    )

    allowance_ids = fields.One2many("cash.allowance", "contract_id", copy=True)

    hdmf_contri_amount = fields.Float(
        string="HDMF Contribution Amount", track_visibility="onchange"
    )
    hourly_rate = fields.Float(
        string="Hourly Rate", help="Hourly Rate", track_visibility="onchange"
    )
    daily_rate = fields.Float(
        string="Daily Rate", help="Daily Rate", track_visibility="onchange"
    )

    tax_shield = fields.Boolean(
        string="Tax Shield",
        help="Enable this to shield the employee from the computation of withholding tax in payslip.",
        default=False,
        track_visibility="onchange",
    )

    daily_wage = fields.Boolean(string="Daily Wage Earner", track_visibility="onchange")
    minimum_wage = fields.Boolean(
        string="Minimum Wage Earner", track_visibility="onchange"
    )

    employee_type = fields.Selection(
        [
            ("regular", "Regular"),
            ("probationary", "Probationary"),
            ("project", "Project Based"),
            ("management", "Management"),
        ],
        track_visibility="onchange",
    )
    work_schedule_type = fields.Selection(
        [("regular", "Regular"), ("ww", "48H WW"), ("fixed", "Fixed"), ("na", "N/A")],
        track_visibility="onchange",
    )
    hours_per_week = fields.Float("Working Hours /week", default=48)
    break_hour_per_day = fields.Float("Break Hours /day", default=1)

    loan_ids = fields.One2many("loan.monitoring", "contract_id", copy=True)

    @api.onchange("wage")
    def onchange_wage(self):
        if self.wage:
            self.daily_rate = (self.wage * self.eemr_months) / self.eemr_days
            self.hourly_rate = (
                (self.wage * self.eemr_months) / self.eemr_days
            ) / self.eemr_hours

    @api.onchange("daily_rate")
    def onchange_daily_rate(self):
        if self.daily_rate:
            self.wage = (self.daily_rate * self.eemr_days) / self.eemr_months
            self.hourly_rate = self.daily_rate / self.eemr_hours

    @api.onchange("hourly_rate")
    def onchange_hourly_rate(self):
        if self.hourly_rate:
            self.wage = (
                self.hourly_rate * self.eemr_hours * self.eemr_days
            ) / self.eemr_months
            self.daily_rate = self.hourly_rate * self.eemr_hours
            
    @api.onchange("company_id")
    def onchange_company_id(self):
        if self.company_id:
            # self.analytic_account_id = False
            # self.accounting_tag_id = False
            self.payroll_type_id = False
            self.payment_type_id = False
            self.employee_type = False
            self.work_schedule_type = False

    def write(self, vals):

        # declaring the existing sched of employee
        employee_sched = self.employee_id.resource_calendar_id.id

        res = super(HrContract, self).write(vals)
        if vals.get("state") == "open":
            self._assign_open_contract()

        # override the auto change of resource_calendar_id in employee
        calendar = vals.get("resource_calendar_id")
        if calendar and (
            self.state == "open"
            or (self.state == "draft" and self.kanban_state == "done")
        ):
            self.mapped("employee_id").write({"resource_calendar_id": employee_sched})

        return res
    
    @api.model
    def create(self, vals):

        contracts = super(HrContract, self).create(vals)
        # print(vals.get('company_id'),self.env.company)
        # if vals.get('company_id') != self.env.company.id:
        #     raise UserError(_('The company in employee record does not match......'))
        employee_search = self.env["hr.employee"].search(
            [("id", "=", vals.get("employee_id"))], limit=1
        )
        if vals.get("company_id") != employee_search.company_id.id:
            raise UserError(_("The company in the employee record does not match."))

        if vals.get("state") == "open":
            contracts._assign_open_contract()
        open_contracts = contracts.filtered(
            lambda c: c.state == "open"
            or c.state == "draft"
            and c.kanban_state == "done"
        )

        # sync contract calendar -> calendar employee
        for contract in open_contracts.filtered(
            lambda c: c.employee_id and c.resource_calendar_id
        ):
            contract.employee_id.resource_calendar_id = contract.resource_calendar_id
        return contracts


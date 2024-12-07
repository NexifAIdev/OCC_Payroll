# -*- coding: utf-8 -*-
# Native Python modules

# Local python modules

# Custom python modules

# Odoo modules
from odoo import models, fields, api, _
from odoo.tools.translate import _
from odoo.exceptions import UserError, ValidationError

class LoanMonitoring(models.Model):
    _name = "loan.monitoring"
    _rec_name = "loan_name"

    contract_id = fields.Many2one(
        "hr.contract", store=True, ondelete="cascade", index=True
    )
    date = fields.Date(string="Loan Date")
    loan_amount = fields.Float(string="Loan Amount")
    loan_payable = fields.Float(string="Loan Payable")
    period_from = fields.Date(string="Period From")
    period_to = fields.Date(string="Period To")
    # monthly_deduction =	fields.Float(string="Deduction Amount")
    monthly_amortization = fields.Float(string="Monthly Amortization")
    monthly_deduction_date = fields.Selection(
        [
            ("every_cutoff", "Every Cutoff"),
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
        help="Loan applied day of the month.",
    )
    initial_paid_amount = fields.Float("Initial Paid Amount")
    paid_amount = fields.Float(
        string="Total Paid Amount", compute="_compute_paid_amount"
    )
    balance = fields.Float(string="Balance", compute="_compute_paid_amount")
    loan_type_id = fields.Many2one("loan.type", string="Loan")
    gl_account = fields.Many2one(
        "account.account", string="GL Account", related="loan_type_id.gl_account"
    )

    is_moved = fields.Boolean(
        string="Moved", track_visibility="onchange", default=False
    )
    loan_name = fields.Char(string="Loan Name", required=True)

    remarks = fields.Char(string="Remarks")

    @api.onchange("loan_type_id")
    def onchange_loan_type_id(self):
        if self.loan_type_id:
            self.gl_account = self.loan_type_id.gl_account.id

    def _compute_paid_amount(self):
        for rec in self:
            # print('not moved')
            rec.paid_amount = 0
            rec.balance = 0
            amount = 0

            ded_auto = self.env["tk.payslip.nontaxable"].search(
                [
                    ("payslip_id.employee_id", "=", rec.contract_id.employee_id.id),
                    ("new_loan_name", "=", rec.loan_name),
                    ("payslip_id.state", "=", "posted"),
                ]
            )
            if ded_auto:
                for d in ded_auto:
                    amount += d.amount_total

            amount = abs(amount)
            rec.paid_amount = amount + rec.initial_paid_amount
            rec.balance = rec.loan_payable - rec.paid_amount
            rec.balance = round(rec.balance, 2)
            if rec.is_moved == True:
                # print('moved')
                rec.balance = 0
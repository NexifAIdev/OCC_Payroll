# -*- coding: utf-8 -*-
# Native Python modules

# Local python modules

# Custom python modules

# Odoo modules
from odoo import models, fields, api, _
from odoo.tools.translate import _
from odoo.exceptions import UserError, ValidationError


class CashAllowance(models.Model):
    _name = "cash.allowance"

    name = fields.Char(string="Description")
    amount = fields.Float(string="Amount")

    taxable = fields.Boolean("Taxable")

    # Allowance applied day of the month for semi-monthly payroll
    allowance_1st_app_date = fields.Selection(
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
        help="Allowance 1st applied day of the month. For semi-monthly",
    )
    allowance_2nd_app_date = fields.Selection(
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
        help="Allowance 2nd applied day of the month. For semi-monthly",
    )

    contract_id = fields.Many2one(
        "hr.contract", "allowance_ids", store=True, ondelete="cascade", index=True
    )


class HrContract(models.Model):
    _inherit = "resource.calendar.attendance"

    year = fields.Selection(
        [
            ("2017", "2017"),
            ("2018", "2018"),
            ("2019", "2019"),
            ("2020", "2020"),
            ("2021", "2021"),
            ("2022", "2022"),
            ("2023", "2023"),
            ("2024", "2024"),
            ("2025", "2025"),
            ("2026", "2026"),
            ("2027", "2027"),
            ("2028", "2028"),
            ("2029", "2029"),
            ("2030", "2030"),
        ],
        string="Year",
    )
    month = fields.Selection(
        [
            ("1", "January"),
            ("2", "February"),
            ("3", "March"),
            ("4", "April"),
            ("5", "May"),
            ("6", "June"),
            ("7", "July"),
            ("8", "August"),
            ("9", "September"),
            ("10", "October"),
            ("11", "November"),
            ("12", "December"),
        ],
        string="Month",
    )

    break_hours = fields.Float(string="Break Hours")

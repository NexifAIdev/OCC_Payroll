# -*- coding: utf-8 -*-
# Native Python modules
from datetime import datetime, date, timedelta

# Local python modules

# Custom python modules

# Odoo modules
from odoo import models, fields, api, _
from odoo.tools.translate import _
from odoo.tools import float_round
from odoo.exceptions import UserError, ValidationError
import odoo.addons.decimal_precision as dp


class HRAccountingConfig(models.Model):
    _name = "hr.accounting.config"

    name = fields.Char()
    company_id = fields.Many2one("res.company", string="Company")

    default_payroll_journal_id = fields.Many2one(
        "account.journal", string="Default Journal"
    )
    default_salaries_exp_account_id = fields.Many2one(
        "account.account", string="Salaries Expense Account"
    )
    default_tax_account_id = fields.Many2one(
        "account.account", string="Withholding Tax Account"
    )
    default_sss_account_id = fields.Many2one(
        "account.account", string="SSS Contribution Account"
    )
    default_phic_account_id = fields.Many2one(
        "account.account", string="PHIC Contribution Account"
    )
    default_hdmf_account_id = fields.Many2one(
        "account.account", string="HDMF Contribution Account"
    )
    default_others_account_id = fields.Many2one(
        "account.account", string="Others Account"
    )
    default_sss_er_account_id = fields.Many2one(
        "account.account", string="SSS ER Contribution Account"
    )
    default_phic_er_account_id = fields.Many2one(
        "account.account", string="PHIC ER Contribution Account"
    )
    default_hdmf_er_account_id = fields.Many2one(
        "account.account", string="HDMF ER Contribution Account"
    )
    default_net_pay_account_id = fields.Many2one("account.account", string="Net Pay")
    default_13th_month_account_id = fields.Many2one(
        "account.account", string="13th Month Pay Account"
    )
    default_13th_payable_account_id = fields.Many2one(
        "account.account", string="13th Month Payable"
    )

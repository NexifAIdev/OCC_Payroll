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


class PayrollAccountingConfig(models.Model):
    _name = "payroll.accounting.config"

    company_id = fields.Many2one("res.company", string="Company")

    default_auto_jv = fields.Boolean(string="Auto Generate JV", default="True")
    default_auto_post = fields.Boolean(string="Auto Post", default="True")
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
    default_13th_month_account_id = fields.Many2one(
        "account.account", string="13th Month Pay Account"
    )

    default_ns_start = fields.Float(string="Night Shift Start")
    default_ns_end = fields.Float(string="Night Shift End")

# -*- coding: utf-8 -*-
# Native Python modules
import calendar

# Local python modules

# Custom python modules

# Odoo modules
from odoo import models, fields, api, _
from odoo.tools.translate import _
from odoo.exceptions import UserError, ValidationError


class SSSTable(models.Model):
    _name = "sss.table"
    _snakecase_name = "sss_table"
    _model_path_name = "occ_payroll.model_sss_table"
    _description = "SSS Table"
    
    name = fields.Char(
        string="Name",
        default=False,
        required=True,
    )
    
    range_of_compensation = fields.Char(
        string="Range of Conpensation",
        default=False,
        required=True,
    )
    
    msc_regular_ss_ec = fields.Float(
        string="Regular SS (EC)",
        default=False,
        required=True,
    )
    
    msc_regular_ss_er = fields.Float(
        string="Regular SS (EC)",
        default=0,
    )
    
    msc_wisp = fields.Float(
        string="WISP",
        default=0,
    )
    
    monthly_salary_credit_total = fields.Float(
        string="Monthly Salary Credit Total",
        default=0,
    )
    
    aoc_regular_ss_er = fields.Float(
        string="Regular SS (ER)",
        default=0,
    )
    
    aoc_regular_ss_ee = fields.Float(
        string="Regular SS (EE)",
        default=0,
    )
    
    aoc_regular_ss_total = fields.Float(
        string="Regular SS (Total)",
        default=0,
    )
    
    aoc_ec_er = fields.Float(
        string="EC (ER)",
        default=0,
    )
    
    aoc_ec_ee = fields.Float(
        string="EC (EE)",
        default=0,
    )
    
    aoc_ec_total = fields.Float(
        string="EC (Total)",
        default=0,
    )
    
    aoc_wisp_er = fields.Float(
        string="WISP (ER)",
        default=0,
    )
    
    aoc_wisp_ee = fields.Float(
        string="WISP (EE)",
        default=0,
    )
    
    aoc_wisp_total = fields.Float(
        string="WISP (Total)",
        default=0,
    )
    
    aoc_total_er = fields.Float(
        string="Total (ER)",
        default=0,
    )
    
    aoc_total_ee = fields.Float(
        string="Total (EE)",
        default=0,
    )
    
    aoc_total_total = fields.Float(
        string="Total (ALL)",
        default=0,
    )   
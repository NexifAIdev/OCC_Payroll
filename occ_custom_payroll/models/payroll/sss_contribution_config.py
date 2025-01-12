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


class SSSContributionConfig(models.Model):
    _name = "sss.contribution.config"
    _description = "SSS Contribution Table"
    _order = "id asc"

    # Range of Compensation
    range_from = fields.Float(string="Range from", help="Range (From) of Compensation.")
    range_to = fields.Float(string="Range to", help="Range (To) of Compensation.")

    # SS Contribution
    er_ss_contri = fields.Float(string="ER (Regular SS)")
    ee_ss_contri = fields.Float(string="EE (Regular SS)")
    total_ss_contri = fields.Float(string="Total (Regular SS)", compute="compute_total")

    er_ec_contri = fields.Float(string="ER (Employee's Compensation)")
    ee_ec_contri = fields.Float(string="EE (Employee's Compensation)")
    total_ec_contri = fields.Float(
        string="Total (Employee's Compensation)", compute="compute_total"
    )

    er_provident_fund = fields.Float(string="ER (Mandatory Provident Fund)")
    ee_provident_fund = fields.Float(string="EE (Mandatory Provident Fund)")
    total_provident_fund = fields.Float(
        string="Total (Mandatory Provident Fund)", compute="compute_total"
    )

    total_er_ss = fields.Float(string="ER Total", compute="compute_total")
    total_ee_ss = fields.Float(string="EE Total", compute="compute_total")
    total_ss = fields.Float(string="Total", compute="compute_total")

    def init(self):
        val = self.env["sss.contribution.config"].search_count([])

        if val == 0:

            vals = [
                {
                    "range_from": 0,
                    "range_to": 3249.99,
                    "er_ss_contri": 255,
                    "ee_ss_contri": 135,
                    "er_ec_contri": 10,
                    "ee_ec_contri": 0,
                    "er_provident_fund": 0,
                    "ee_provident_fund": 0,
                },
                {
                    "range_from": 3250.00,
                    "range_to": 3749.99,
                    "er_ss_contri": 297.50,
                    "ee_ss_contri": 157.50,
                    "er_ec_contri": 10,
                    "ee_ec_contri": 0,
                    "er_provident_fund": 0,
                    "ee_provident_fund": 0,
                },
                {
                    "range_from": 3750.00,
                    "range_to": 4249.99,
                    "er_ss_contri": 340,
                    "ee_ss_contri": 180,
                    "er_ec_contri": 10,
                    "ee_ec_contri": 0,
                    "er_provident_fund": 0,
                    "ee_provident_fund": 0,
                },
                {
                    "range_from": 4250.00,
                    "range_to": 4749.99,
                    "er_ss_contri": 382.50,
                    "ee_ss_contri": 202.50,
                    "er_ec_contri": 10,
                    "ee_ec_contri": 0,
                    "er_provident_fund": 0,
                    "ee_provident_fund": 0,
                },
                {
                    "range_from": 4750.00,
                    "range_to": 5249.99,
                    "er_ss_contri": 425,
                    "ee_ss_contri": 225,
                    "er_ec_contri": 10,
                    "ee_ec_contri": 0,
                    "er_provident_fund": 0,
                    "ee_provident_fund": 0,
                },
                {
                    "range_from": 5250.00,
                    "range_to": 5749.99,
                    "er_ss_contri": 467.50,
                    "ee_ss_contri": 247.50,
                    "er_ec_contri": 10,
                    "ee_ec_contri": 0,
                    "er_provident_fund": 0,
                    "ee_provident_fund": 0,
                },
                {
                    "range_from": 5750.00,
                    "range_to": 6249.99,
                    "er_ss_contri": 510,
                    "ee_ss_contri": 270,
                    "er_ec_contri": 10,
                    "ee_ec_contri": 0,
                    "er_provident_fund": 0,
                    "ee_provident_fund": 0,
                },
                {
                    "range_from": 6250,
                    "range_to": 6749.99,
                    "er_ss_contri": 552.5,
                    "ee_ss_contri": 292.5,
                    "er_ec_contri": 10,
                    "ee_ec_contri": 0,
                    "er_provident_fund": 0,
                    "ee_provident_fund": 0,
                },
                {
                    "range_from": 6750,
                    "range_to": 7249.99,
                    "er_ss_contri": 595,
                    "ee_ss_contri": 315,
                    "er_ec_contri": 10,
                    "ee_ec_contri": 0,
                    "er_provident_fund": 0,
                    "ee_provident_fund": 0,
                },
                {
                    "range_from": 7250,
                    "range_to": 7749.99,
                    "er_ss_contri": 637.5,
                    "ee_ss_contri": 337.5,
                    "er_ec_contri": 10,
                    "ee_ec_contri": 0,
                    "er_provident_fund": 0,
                    "ee_provident_fund": 0,
                },
                {
                    "range_from": 7750,
                    "range_to": 8249.99,
                    "er_ss_contri": 680,
                    "ee_ss_contri": 360,
                    "er_ec_contri": 10,
                    "ee_ec_contri": 0,
                    "er_provident_fund": 0,
                    "ee_provident_fund": 0,
                },
                {
                    "range_from": 8250,
                    "range_to": 8749.99,
                    "er_ss_contri": 722.5,
                    "ee_ss_contri": 382.5,
                    "er_ec_contri": 10,
                    "ee_ec_contri": 0,
                    "er_provident_fund": 0,
                    "ee_provident_fund": 0,
                },
                {
                    "range_from": 8750,
                    "range_to": 9249.99,
                    "er_ss_contri": 765,
                    "ee_ss_contri": 405,
                    "er_ec_contri": 10,
                    "ee_ec_contri": 0,
                    "er_provident_fund": 0,
                    "ee_provident_fund": 0,
                },
                {
                    "range_from": 9250,
                    "range_to": 9749.99,
                    "er_ss_contri": 807.5,
                    "ee_ss_contri": 427.5,
                    "er_ec_contri": 10,
                    "ee_ec_contri": 0,
                    "er_provident_fund": 0,
                    "ee_provident_fund": 0,
                },
                {
                    "range_from": 9750,
                    "range_to": 0249.99,
                    "er_ss_contri": 850,
                    "ee_ss_contri": 450,
                    "er_ec_contri": 10,
                    "ee_ec_contri": 0,
                    "er_provident_fund": 0,
                    "ee_provident_fund": 0,
                },
                {
                    "range_from": 10250,
                    "range_to": 10749.99,
                    "er_ss_contri": 892.5,
                    "ee_ss_contri": 472.5,
                    "er_ec_contri": 10,
                    "ee_ec_contri": 0,
                    "er_provident_fund": 0,
                    "ee_provident_fund": 0,
                },
                {
                    "range_from": 10750,
                    "range_to": 11249.99,
                    "er_ss_contri": 935,
                    "ee_ss_contri": 495,
                    "er_ec_contri": 10,
                    "ee_ec_contri": 0,
                    "er_provident_fund": 0,
                    "ee_provident_fund": 0,
                },
                {
                    "range_from": 11250,
                    "range_to": 11749.99,
                    "er_ss_contri": 977.5,
                    "ee_ss_contri": 517.5,
                    "er_ec_contri": 10,
                    "ee_ec_contri": 0,
                    "er_provident_fund": 0,
                    "ee_provident_fund": 0,
                },
                {
                    "range_from": 11750,
                    "range_to": 12249.99,
                    "er_ss_contri": 1020,
                    "ee_ss_contri": 540,
                    "er_ec_contri": 10,
                    "ee_ec_contri": 0,
                    "er_provident_fund": 0,
                    "ee_provident_fund": 0,
                },
                {
                    "range_from": 12250,
                    "range_to": 12749.99,
                    "er_ss_contri": 1062.5,
                    "ee_ss_contri": 562.5,
                    "er_ec_contri": 10,
                    "ee_ec_contri": 0,
                    "er_provident_fund": 0,
                    "ee_provident_fund": 0,
                },
                {
                    "range_from": 12750,
                    "range_to": 13249.99,
                    "er_ss_contri": 1105,
                    "ee_ss_contri": 585,
                    "er_ec_contri": 10,
                    "ee_ec_contri": 0,
                    "er_provident_fund": 0,
                    "ee_provident_fund": 0,
                },
                {
                    "range_from": 13250,
                    "range_to": 13749.99,
                    "er_ss_contri": 1147.5,
                    "ee_ss_contri": 607.5,
                    "er_ec_contri": 10,
                    "ee_ec_contri": 0,
                    "er_provident_fund": 0,
                    "ee_provident_fund": 0,
                },
                {
                    "range_from": 13750,
                    "range_to": 14249.99,
                    "er_ss_contri": 1190,
                    "ee_ss_contri": 630,
                    "er_ec_contri": 10,
                    "ee_ec_contri": 0,
                    "er_provident_fund": 0,
                    "ee_provident_fund": 0,
                },
                {
                    "range_from": 14250,
                    "range_to": 14749.99,
                    "er_ss_contri": 1232.5,
                    "ee_ss_contri": 652.5,
                    "er_ec_contri": 10,
                    "ee_ec_contri": 0,
                    "er_provident_fund": 0,
                    "ee_provident_fund": 0,
                },
                {
                    "range_from": 14750,
                    "range_to": 15249.99,
                    "er_ss_contri": 1275,
                    "ee_ss_contri": 675,
                    "er_ec_contri": 30,
                    "ee_ec_contri": 0,
                    "er_provident_fund": 0,
                    "ee_provident_fund": 0,
                },
                {
                    "range_from": 15250,
                    "range_to": 15749.99,
                    "er_ss_contri": 1317.5,
                    "ee_ss_contri": 697.5,
                    "er_ec_contri": 30,
                    "ee_ec_contri": 0,
                    "er_provident_fund": 0,
                    "ee_provident_fund": 0,
                },
                {
                    "range_from": 15750,
                    "range_to": 16249.99,
                    "er_ss_contri": 1360,
                    "ee_ss_contri": 720,
                    "er_ec_contri": 30,
                    "ee_ec_contri": 0,
                    "er_provident_fund": 0,
                    "ee_provident_fund": 0,
                },
                {
                    "range_from": 16250,
                    "range_to": 16749.99,
                    "er_ss_contri": 1402.5,
                    "ee_ss_contri": 742.5,
                    "er_ec_contri": 30,
                    "ee_ec_contri": 0,
                    "er_provident_fund": 0,
                    "ee_provident_fund": 0,
                },
                {
                    "range_from": 16750,
                    "range_to": 17249.99,
                    "er_ss_contri": 1445,
                    "ee_ss_contri": 765,
                    "er_ec_contri": 30,
                    "ee_ec_contri": 0,
                    "er_provident_fund": 0,
                    "ee_provident_fund": 0,
                },
                {
                    "range_from": 17250,
                    "range_to": 17749.99,
                    "er_ss_contri": 1487.5,
                    "ee_ss_contri": 787.5,
                    "er_ec_contri": 30,
                    "ee_ec_contri": 0,
                    "er_provident_fund": 0,
                    "ee_provident_fund": 0,
                },
                {
                    "range_from": 17750,
                    "range_to": 18249.99,
                    "er_ss_contri": 1530,
                    "ee_ss_contri": 810,
                    "er_ec_contri": 30,
                    "ee_ec_contri": 0,
                    "er_provident_fund": 0,
                    "ee_provident_fund": 0,
                },
                {
                    "range_from": 18250,
                    "range_to": 18749.99,
                    "er_ss_contri": 1572.5,
                    "ee_ss_contri": 832.5,
                    "er_ec_contri": 30,
                    "ee_ec_contri": 0,
                    "er_provident_fund": 0,
                    "ee_provident_fund": 0,
                },
                {
                    "range_from": 18750,
                    "range_to": 19249.99,
                    "er_ss_contri": 1615,
                    "ee_ss_contri": 855,
                    "er_ec_contri": 30,
                    "ee_ec_contri": 0,
                    "er_provident_fund": 0,
                    "ee_provident_fund": 0,
                },
                {
                    "range_from": 19250,
                    "range_to": 19749.99,
                    "er_ss_contri": 1657.5,
                    "ee_ss_contri": 877.5,
                    "er_ec_contri": 30,
                    "ee_ec_contri": 0,
                    "er_provident_fund": 0,
                    "ee_provident_fund": 0,
                },
                {
                    "range_from": 19750,
                    "range_to": 20249.99,
                    "er_ss_contri": 1700,
                    "ee_ss_contri": 900,
                    "er_ec_contri": 30,
                    "ee_ec_contri": 0,
                    "er_provident_fund": 0,
                    "ee_provident_fund": 0,
                },
                {
                    "range_from": 20250,
                    "range_to": 20749.99,
                    "er_ss_contri": 1700,
                    "ee_ss_contri": 900,
                    "er_ec_contri": 30,
                    "ee_ec_contri": 0,
                    "er_provident_fund": 42.5,
                    "ee_provident_fund": 22.5,
                },
                {
                    "range_from": 20750,
                    "range_to": 21249.99,
                    "er_ss_contri": 1700,
                    "ee_ss_contri": 900,
                    "er_ec_contri": 30,
                    "ee_ec_contri": 0,
                    "er_provident_fund": 85,
                    "ee_provident_fund": 45,
                },
                {
                    "range_from": 21250,
                    "range_to": 21749.99,
                    "er_ss_contri": 1700,
                    "ee_ss_contri": 900,
                    "er_ec_contri": 30,
                    "ee_ec_contri": 0,
                    "er_provident_fund": 127.5,
                    "ee_provident_fund": 67.5,
                },
                {
                    "range_from": 21750,
                    "range_to": 22249.99,
                    "er_ss_contri": 1700,
                    "ee_ss_contri": 900,
                    "er_ec_contri": 30,
                    "ee_ec_contri": 0,
                    "er_provident_fund": 170,
                    "ee_provident_fund": 90,
                },
                {
                    "range_from": 22250,
                    "range_to": 22749.99,
                    "er_ss_contri": 1700,
                    "ee_ss_contri": 900,
                    "er_ec_contri": 30,
                    "ee_ec_contri": 0,
                    "er_provident_fund": 212.5,
                    "ee_provident_fund": 112.5,
                },
                {
                    "range_from": 22750,
                    "range_to": 23249.99,
                    "er_ss_contri": 1700,
                    "ee_ss_contri": 900,
                    "er_ec_contri": 30,
                    "ee_ec_contri": 0,
                    "er_provident_fund": 255,
                    "ee_provident_fund": 135,
                },
                {
                    "range_from": 23250,
                    "range_to": 23749.99,
                    "er_ss_contri": 1700,
                    "ee_ss_contri": 900,
                    "er_ec_contri": 30,
                    "ee_ec_contri": 0,
                    "er_provident_fund": 297.5,
                    "ee_provident_fund": 157.5,
                },
                {
                    "range_from": 23750,
                    "range_to": 24249.99,
                    "er_ss_contri": 1700,
                    "ee_ss_contri": 900,
                    "er_ec_contri": 30,
                    "ee_ec_contri": 0,
                    "er_provident_fund": 340,
                    "ee_provident_fund": 180,
                },
                {
                    "range_from": 24250,
                    "range_to": 24749.99,
                    "er_ss_contri": 1700,
                    "ee_ss_contri": 900,
                    "er_ec_contri": 30,
                    "ee_ec_contri": 0,
                    "er_provident_fund": 382.5,
                    "ee_provident_fund": 202.5,
                },
                {
                    "range_from": 24750,
                    "range_to": 9999999,
                    "er_ss_contri": 1700,
                    "ee_ss_contri": 900,
                    "er_ec_contri": 30,
                    "ee_ec_contri": 0,
                    "er_provident_fund": 425,
                    "ee_provident_fund": 225,
                },
            ]

            for x in vals:
                self.env["sss.contribution.config"].create(x)

    # @api.onchange('er_ss_contri','ee_ss_contri','er_ec_contri','ee_ec_contri','er_provident_fund','ee_provident_fund')
    def compute_total(self):
        for rec in self:
            rec.total_ss_contri = rec.er_ss_contri + rec.ee_ss_contri
            rec.total_ec_contri = rec.er_ec_contri + rec.ee_ec_contri
            rec.total_provident_fund = rec.er_provident_fund + rec.ee_provident_fund
            rec.total_er_ss = (
                rec.er_ss_contri + rec.er_ec_contri + rec.er_provident_fund
            )
            rec.total_ee_ss = (
                rec.ee_ss_contri + rec.ee_ec_contri + rec.ee_provident_fund
            )
            rec.total_ss = rec.total_ee_ss + rec.total_er_ss

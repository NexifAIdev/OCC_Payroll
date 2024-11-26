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

class WithholdingTaxConfig(models.Model):
    _name = "withholding.tax.config"
    _order = "id asc"

    # payroll_type = fields.Selection([('daily','Daily'),('weekly','Weekly'),('semi-monthly','Semi-monthly'),('monthly','Monthly')], string="Payroll Type", default='semi-monthly')
    payroll_type_id = fields.Many2one("payroll.type", string="Payroll Type")

    # Range of Compensation
    range_from = fields.Float(
        string="Range from", help="Range (From) of Compensation Level."
    )
    range_to = fields.Float(string="Range to", help="Range (To) of Compensation Level.")

    x_value = fields.Float(string="x")
    y_value = fields.Float(string="y")
    z_value = fields.Float(string="z")

    complete_formula = fields.Char(string="Prescribed Minimum Withholding Tax")

    @api.onchange("x_value", "y_value", "z_value")
    def set_formula(self):
        if self.x_value == 0.0 and self.y_value == 0.0 and self.z_value == 0.0:
            self.complete_formula = "0.00"

        else:
            val = """%.2f + %.2f%% over %.2f""" % (
                self.x_value,
                self.y_value,
                self.z_value,
            )

            self.complete_formula = val

    def init(self):
        val = self.env["withholding.tax.config"].search_count([])

        if val == 0:
            ptype_id = self.env["payroll.type"].search(
                [("name", "=", "Weekly")], limit=1
            )

            if ptype_id:
                vals = [
                    {
                        "payroll_type_id": ptype_id.id,
                        "range_from": 0.00,
                        "range_to": 4807.00,
                        "x_value": 0,
                        "y_value": 0,
                        "z_value": 0,
                    },
                    {
                        "payroll_type_id": ptype_id.id,
                        "range_from": 4808.00,
                        "range_to": 7691.00,
                        "x_value": 0,
                        "y_value": 20,
                        "z_value": 4808.00,
                    },
                    {
                        "payroll_type_id": ptype_id.id,
                        "range_from": 7692.00,
                        "range_to": 15384.00,
                        "x_value": 576.92,
                        "y_value": 25,
                        "z_value": 7692.00,
                    },
                    {
                        "payroll_type_id": ptype_id.id,
                        "range_from": 15385.00,
                        "range_to": 38461.00,
                        "x_value": 2500.00,
                        "y_value": 30,
                        "z_value": 15385.00,
                    },
                    {
                        "payroll_type_id": ptype_id.id,
                        "range_from": 38462.00,
                        "range_to": 153845.00,
                        "x_value": 9423.08,
                        "y_value": 32,
                        "z_value": 38462.00,
                    },
                    {
                        "payroll_type_id": ptype_id.id,
                        "range_from": 153846.00,
                        "range_to": 9999999.00,
                        "x_value": 46346.15,
                        "y_value": 35,
                        "z_value": 153846.00,
                    },
                ]

                for x in vals:
                    data = self.env["withholding.tax.config"].create(x)
                    data.set_formula()
            else:
                # add warning here
                print("No payroll type - Semi-Monthly")

            ptype_id = self.env["payroll.type"].search(
                [("name", "=", "Semi-Monthly")], limit=1
            )

            if ptype_id:
                vals = [
                    {
                        "payroll_type_id": ptype_id.id,
                        "range_from": 0.00,
                        "range_to": 10416.00,
                        "x_value": 0,
                        "y_value": 0,
                        "z_value": 0,
                    },
                    {
                        "payroll_type_id": ptype_id.id,
                        "range_from": 10417.00,
                        "range_to": 16666.00,
                        "x_value": 0,
                        "y_value": 20,
                        "z_value": 10417.00,
                    },
                    {
                        "payroll_type_id": ptype_id.id,
                        "range_from": 16667.00,
                        "range_to": 33332.00,
                        "x_value": 1250.00,
                        "y_value": 25,
                        "z_value": 16667.00,
                    },
                    {
                        "payroll_type_id": ptype_id.id,
                        "range_from": 33333.00,
                        "range_to": 83332.00,
                        "x_value": 5416.67,
                        "y_value": 30,
                        "z_value": 33333.00,
                    },
                    {
                        "payroll_type_id": ptype_id.id,
                        "range_from": 83333.00,
                        "range_to": 333332.00,
                        "x_value": 20416.67,
                        "y_value": 32,
                        "z_value": 83333.00,
                    },
                    {
                        "payroll_type_id": ptype_id.id,
                        "range_from": 333333.00,
                        "range_to": 9999999.00,
                        "x_value": 100416.67,
                        "y_value": 35,
                        "z_value": 333333.00,
                    },
                ]

                for x in vals:
                    data = self.env["withholding.tax.config"].create(x)
                    data.set_formula()
            else:
                # add warning here
                print("No payroll type - Semi-Monthly")

            ptype_id = self.env["payroll.type"].search(
                [("name", "=", "Monthly")], limit=1
            )

            if ptype_id:
                vals = [
                    {
                        "payroll_type_id": ptype_id.id,
                        "range_from": 0.00,
                        "range_to": 20832.00,
                        "x_value": 0,
                        "y_value": 0,
                        "z_value": 0,
                    },
                    {
                        "payroll_type_id": ptype_id.id,
                        "range_from": 20833.00,
                        "range_to": 33332.00,
                        "x_value": 0,
                        "y_value": 20,
                        "z_value": 20833.00,
                    },
                    {
                        "payroll_type_id": ptype_id.id,
                        "range_from": 33333.00,
                        "range_to": 66666.00,
                        "x_value": 2500.00,
                        "y_value": 25,
                        "z_value": 33333.00,
                    },
                    {
                        "payroll_type_id": ptype_id.id,
                        "range_from": 66667.00,
                        "range_to": 166666.00,
                        "x_value": 10833.33,
                        "y_value": 30,
                        "z_value": 66667.00,
                    },
                    {
                        "payroll_type_id": ptype_id.id,
                        "range_from": 166667.00,
                        "range_to": 666666.00,
                        "x_value": 40833.33,
                        "y_value": 32,
                        "z_value": 166667.00,
                    },
                    {
                        "payroll_type_id": ptype_id.id,
                        "range_from": 666667.00,
                        "range_to": 9999999.00,
                        "x_value": 200833.33,
                        "y_value": 35,
                        "z_value": 666667.00,
                    },
                ]

                for x in vals:
                    data = self.env["withholding.tax.config"].create(x)
                    data.set_formula()
            else:
                # add warning here
                print("No payroll type - Monthly")

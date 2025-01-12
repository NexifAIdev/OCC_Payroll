# -*- coding: utf-8 -*-
# Native Python modules

# Local python modules

# Custom python modules

# Odoo modules
from odoo import models, fields, api, _
from odoo.tools.translate import _
from odoo.exceptions import UserError, ValidationError


class EmployeeRelationshipLine(models.Model):
    _name = "employee.relationship.line"
    _description = "Employee Relationship Line"

    @api.model
    def _list_all_employee(self):
        self._cr.execute(
            """ SELECT he."id"::VARCHAR, he."name"::VARCHAR FROM hr_employee he WHERE he.active = True AND he."id" != 1 ORDER BY he.name ASC """
        )
        return self._cr.fetchall()

    name = fields.Selection(
        string="Name", selection="_list_all_employee", required=True
    )
    relationship_id = fields.Many2one("hr.relationship", string="Relationship")
    employee_id = fields.Many2one("hr.employee", string="Employee", ondelete="cascade")

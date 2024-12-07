# -*- coding: utf-8 -*-
# Native Python modules

# Local python modules

# Custom python modules

# Odoo modules
from odoo import models, fields, api, _
from odoo.tools.translate import _
from odoo.exceptions import UserError, ValidationError

class HrEmployeeEducation(models.Model):
    _name = "hr.employee.education"

    employee_id = fields.Many2one(
        comodel_name="hr.employee", 
        string="Employee ID", 
        ondelete="cascade",
    )

    acad_level = fields.Selection(
        [
            ("hsg", "High School Graduate"),
            ("vocation", "Vocational"),
            ("college", "College Undergraduate"),
            ("associate", "Associate Degree"),
            ("bs", "Bachelor's Degree"),
            ("ms", "Master's Degree"),
            ("phd", "Doctoral Degree"),
        ]
    )
    school_id = fields.Many2one(
        comodel_name="hr.schools", 
        string="School",
    )
    degree_id = fields.Many2one(
        comodel_name="hr.degree", 
        string="Degree Obtained",
    )
    honors = fields.Char(
        string="Honors Received"
    )
    started_date = fields.Date(
        string="Start Date"
    )
    ended_date = fields.Date(
        string="End Date"
    )
    units = fields.Char(
        string="Units Earned"
    )
    major = fields.Char(
        string="Major"
    )
    minor = fields.Char(
        string="Minor"
    )
    degree_type_id = fields.Many2one(
        comodel_name="hr.degree", 
        string="Degree Type",    
    )
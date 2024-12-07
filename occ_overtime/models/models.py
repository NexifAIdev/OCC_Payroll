from odoo import models, fields

class occ_hr_overtime(models.Model):
    _name = 'hr_overtime'
    _description = 'HR Overtime'

    employee_id = fields.Many2one("hr.employee", string="Employee")
    approver_id = fields.Many2one("hr.employee", string="Approver")
    start_date = fields.Datetime(string='Start Date')
    end_date = fields.Datetime(string='End Date')
    ot_type = fields.Selection([
        ('rdot', "Rest Day OT"),
        ('nrdot', "Non Rest Day OT")
    ], string="OT Type")

    is_valid_range = fields.Boolean(compute='_compute_is_valid_range')

    def _compute_is_valid_range(self):
        for record in self:
            record.is_valid_range = (
                record.start_date <= record.end_date
                if record.start_date and record.end_date
                else True
            )
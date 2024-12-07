from odoo import models, fields, api

class OCCOvertime(models.Model):
    _inherit = "hr.overtime"

    state = fields.Selection(selection_add=[('draft', 'Draft'),
                              ('approver1', 'Approver1'),
                              ('approver2', 'Approver2'),
                              ('approved',"Approved"),
                              ('refused', 'Refused')], string="state",
                             default="draft", help="State of the overtime "
                                                   "request.")
    
    approver1 = fields.Many2one('hr.employee', string="Approver 1", compute="_compute_approver1", store=True)
    approver2 = fields.Many2one('hr.employee', string="Approver 2", compute="_compute_approver2", store=True)

    @api.depends('employee_id')
    def _compute_approver1(self):
        for record in self:
            if record.employee_id:
                record.approver1 = record.employee_id.parent_id

    @api.depends('employee_id')
    def _compute_approver2(self):
        for record in self:
            if record.employee_id:
                record.approver2 = record.employee_id.approver2_id

    def action_submit(self):    
        return self.write({'state':'approver1'})
    
    def action_approve1(self):
        approver2 = self.employee_id.parent_id
        if approver2:
            return self.write({'state':'approver2'})
        else:
            super(OCCOvertime, self).action_approve()
            return
            
    def action_approve2(self):
        super(OCCOvertime, self).action_approve()
        return
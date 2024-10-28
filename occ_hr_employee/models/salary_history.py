from odoo import models, fields, api

class SalaryHistory(models.Model):
    _name = 'salary.history'
    _description = "Salary History"

    employee_id = fields.Many2one('hr.employee', string="Employee", required = True)
    date_from = fields.Date("Date From")
    base_salary = fields.Monetary("Base Salary", currency_field='currency_id')
    de_minimis = fields.Monetary("De Minimis", currency_field='currency_id')
    monthly_gross = fields.Monetary("Monthly Gross", currency_field='currency_id')
    percentage_increase = fields.Float("Percentage Increase")
    increase_amt = fields.Float("Increase Amt")
    raise_percent = fields.Float("Raise %")
    commission = fields.Float("Commission")
    notes = fields.Text("Notes")
    currency_id = fields.Many2one('res.currency', string='Currency', required=True, default=lambda self: self.env.company.currency_id)
class EmployeeSalary(models.Model):
    _inherit = "hr.employee"

    #Payroll Information
    salary_history_ids = fields.One2many('salary.history', 'employee_id', string='Salary History')

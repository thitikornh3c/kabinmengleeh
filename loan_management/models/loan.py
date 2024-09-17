from odoo import models, fields

class Loan(models.Model):
    _name = 'loan.management'
    _description = 'Loan Management'

    name = fields.Char(string='Loan Name', required=True)
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True)
    amount = fields.Float(string='Loan Amount', required=True)
    date_start = fields.Date(string='Start Date', required=True)
    installments = fields.One2many('loan.installment', 'loan_id', string='Installments')
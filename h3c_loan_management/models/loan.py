from odoo import models, fields

class Loan(models.Model):
    _name = 'loan.management'
    _description = 'Loan Management'

    name = fields.Char(string='Loan Reference', required=True, copy=False, readonly=True, default=lambda self: _('New'))
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True)
    amount = fields.Float(string='Loan Amount', required=True)
    installment_ids = fields.One2many('loan.installment', 'loan_id', string='Installments')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('approved', 'Approved'),
        ('repaying', 'Repaying'),
        ('done', 'Done'),
    ], string='Status', readonly=True, default='draft')
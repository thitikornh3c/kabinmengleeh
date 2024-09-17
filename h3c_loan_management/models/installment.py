from odoo import models, fields

class Installment(models.Model):
    _name = 'loan.installment'
    _description = 'Loan Installment'

    name = fields.Char(string='Installment Reference', required=True, copy=False, readonly=True, default=lambda self: _('New'))
    loan_id = fields.Many2one('loan.management', string='Loan', required=True)
    amount = fields.Float(string='Installment Amount', required=True)
    due_date = fields.Date(string='Due Date')
    state = fields.Selection([
        ('pending', 'Pending'),
        ('paid', 'Paid'),
    ], string='Status', readonly=True, default='pending')
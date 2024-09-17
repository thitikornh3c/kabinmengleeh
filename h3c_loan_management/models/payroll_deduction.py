from odoo import models, fields

class PayrollStructure(models.Model):
    _inherit = 'hr.payroll.structure'

    loan_deduction_ids = fields.One2many('loan.deduction', 'structure_id', string='Loan Deductions')

class LoanDeduction(models.Model):
    _name = 'loan.deduction'
    _description = 'Loan Deduction'

    name = fields.Char(string='Description', required=True)
    loan_id = fields.Many2one('loan.management', string='Loan', required=True)
    amount = fields.Float(string='Amount', required=True)
    structure_id = fields.Many2one('hr.payroll.structure', string='Payroll Structure')
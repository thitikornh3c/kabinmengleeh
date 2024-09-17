from odoo import models, fields

class LoanInstallment(models.Model):
    _name = 'loan.installment'
    _description = 'Loan Installment'

    name = fields.Char(string='Installment Reference', required=True)
    loan_id = fields.Many2one('loan.management', string='Loan', required=True)
    installment_amount = fields.Float(string='Installment Amount', required=True)
    due_date = fields.Date(string='Due Date', required=True)
    paid = fields.Boolean(string='Paid', default=False)

    @api.model
    def create(self, vals):
        record = super(LoanInstallment, self).create(vals)
        # Logic to create a salary deduction based on this installment
        if not record.paid:
            self.env['hr.payslip'].create({
                'employee_id': record.loan_id.employee_id.id,
                'date_from': record.due_date,
                'date_to': record.due_date,
                'line_ids': [(0, 0, {
                    'name': 'Loan Deduction',
                    'contract_id': record.loan_id.employee_id.contract_id.id,
                    'category_id': self.env.ref('hr_payroll.salary_structure_category').id,
                    'amount': -record.installment_amount,
                })]
            })
        return record
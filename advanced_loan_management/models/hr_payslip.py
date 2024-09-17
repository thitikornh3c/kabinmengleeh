from odoo import models, fields, api

class HRPayslip(models.Model):
    _inherit = 'hr.payslip'

    @api.model
    def create(self, vals):
        # Override create method to automatically add loan deduction rule
        res = super(HRPayslip, self).create(vals)
        if res:
            # Compute loan deductions and create corresponding salary lines
            res.compute_loan_deductions()
        return res

    def compute_loan_deductions(self):
        for slip in self:
            # Fetch active loan contracts for the employee
            loan_contracts = self.env['loan.contract'].search([
                ('employee_id', '=', slip.employee_id.id),
                ('state', '=', 'active')
            ])
            
            for loan in loan_contracts:
                # Example: Deduct 10% of the loan amount
                deduction_amount = loan.amount * 0.10

                # Add deduction as a salary line
                self.env['hr.payslip.line'].create({
                    'payslip_id': slip.id,
                    'salary_rule_id': self.env.ref('your_module.salary_rule_loan_deduction').id,
                    'amount': -deduction_amount,
                    'sequence': 10,  # Adjust sequence if needed
                })

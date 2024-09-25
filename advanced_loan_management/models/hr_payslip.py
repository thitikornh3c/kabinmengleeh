from odoo import models, fields, api

class HRPayslip(models.Model):
    _inherit = 'hr.payslip'

    move_type = fields.Selection([
        ('out_invoice', 'Invoice Out'),
        ('in_invoice', 'Invoice In'),
        ('slip', 'Slip')
    ], string='Move Type')

    @api.model
    def compute_sheet(self):
        super(HRPayslip, self).compute_sheet()
        
        for slip in self:
            loan_contracts = self.env['loan.request'].search([
                ('partner_id', '=', 'Emp3') #slip.employee_id.id
                # ('state', '=', 'active')
            ])
            # Access the custom input from employee record
            # custom_input = slip.employee_id.custom_input
            
            # Apply custom logic using the additional input
            # For example, you might want to add a custom amount to the payslip
            amonthSalary = 0
            totalOther = 0
            for line in slip.line_ids:
                if line.salary_rule_id.code == 'BASIC':
                    workDataAmount = line.amount
                    amonthSalary =  workDataAmount * 21
                    line.amount = amonthSalary
                    line.total = amonthSalary
                if line.salary_rule_id.code == 'GROSS':
                    line.amount = amonthSalary
                    line.total = amonthSalary
                elif line.salary_rule_id.code == 'LOAN_DEDUCTION':
                    totalOther = -1000
                    line.amount = totalOther
                    line.total = totalOther
                    line.name = loan_contracts[0]
                    for loan in loan_contracts:
                        line.name = loan
                else:
                    totalOther = totalOther + line.amount
                    line.name = f'{line.name} {line.amount}'

            # Loop re calculate
            for line in slip.line_ids:
                if line.salary_rule_id.code == 'NET':
                    workDataAmount = line.amount
                    line.amount = amonthSalary + totalOther
                    line.total = amonthSalary + totalOther

    # def prepare_report_data(self):
    #     # Ensure the attribute `move_type` is present if required
    #     records = self.env['hr.payslip'].search([])
    #     for record in records:
    #         if not hasattr(record, 'move_type'):
    #             record.move_type = None  # Default value if not present
    #     return records
    # @api.model
    # def create(self, vals):
    #     # Override create method to automatically add loan deduction rule
    #     res = super(HRPayslip, self).create(vals)
    #     if res:
    #         # Compute loan deductions and create corresponding salary lines
    #         res.compute_loan_deductions()
    #     return res

    # def compute_loan_deductions(self):
    #     for slip in self:
    #         # Fetch active loan contracts for the employee
    #         print(slip.employee_id.id)
    #         loan_contracts = self.env['loan.request'].search([
    #             ('partner_id', '=', slip.employee_id.id)
    #             # ('state', '=', 'active')
    #         ])
    #         print(loan_contracts)
    #         for loan in loan_contracts:
    #             # Example: Deduct 10% of the loan amount
    #             deduction_amount = loan.amount * 0.10

    #             # Add deduction as a salary line
    #             self.env['hr.payslip.line'].create({
    #                 'payslip_id': slip.id,
    #                 'salary_rule_id': 26,
    #                 'amount': -deduction_amount,
    #                 'sequence': 10,  # Adjust sequence if needed
    #             })

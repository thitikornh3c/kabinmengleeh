from odoo import models, fields, api
import logging
import json

_logger = logging.getLogger(__name__)

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
            _logger.info(f"Processing payslip for employee ID: {slip.employee_id.id}")
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
            sso_amount = 0


            work_entries = self.env['hr.work.entry'].search([
                ('employee_id', '=', slip.employee_id.id),
                ('date_start', '>=', slip.date_from),
                ('date_stop', '<=', slip.date_to)
            ])


            contract = self.env['hr.contract'].search([
                ('employee_id', '=', slip.employee_id.id),
                ('state', '=', 'open')  # Only get active contracts
            ], limit=1)


            workdays_count = 0
            for entry in work_entries:
                # Calculate number of days in each work entry
                if entry.date_start and entry.date_stop:
                    start_date = fields.Date.from_string(entry.date_start)
                    end_date = fields.Date.from_string(entry.date_stop)
                    _logger.info(f"Processing payslip for work entry: {entry.code} {entry.duration} {entry.date_start} {entry.date_stop} || {start_date} {end_date}")
                    # delta_days = (end_date - start_date).days + 1  # Include both start and end dates
                    # workdays_count += delta_days


            scheduled_workdays_count = 0
            for line in slip.worked_days_line_ids:
                _logger.info(f"Processing payslip for attendance: {line} {line.number_of_days}")
                if line.work_entry_type_id.code == 'WORK100':
                    scheduled_workdays_count = line.number_of_days
                    # line.number_of_days = 20
                    line.amount = line.number_of_days * contract.wage
            
            for line in slip.line_ids:

                # _logger.info(f"Processing payslip line of employee {slip.employee_id.id}: {number_of_days}")
                if line.salary_rule_id.code == 'BASIC':
                    # loan_contracts = self.env['loan.request'].search([
                    #     ('partner_id', '=', slip.employee_id.id)
                    # ])
                    # loan_contracts_data = loan_contracts.read(['id', 'amount', 'state'])

                    # Get scheduled workdays for the employee

                    _logger.info(f"Processing payslip for employee attendance: {scheduled_workdays_count}")

                    workDataAmount = line.amount
                    amonthSalary =  workDataAmount * scheduled_workdays_count
                    line.amount = amonthSalary
                    line.total = amonthSalary
                elif line.salary_rule_id.code == 'GROSS':
                    line.amount = amonthSalary
                    line.total = amonthSalary
                elif line.salary_rule_id.code == 'SSO':
                    sso_amount = amonthSalary * 0.05 
                    if sso_amount > 750:
                        sso_amount = -750
                    else:
                        sso_amount = -sso_amount
                    line.amount = sso_amount
                    line.total = sso_amount
                elif line.salary_rule_id.code == 'LOAN_DEDUCTION':
                    loan = -1000
                    totalOther = totalOther + loan
                    line.amount = loan
                    line.total = loan
                    line.name = f'{line.name} ({loan_contracts[0].id})'
                    # for loan in loan_contracts:
                    #     line.name = loan
                else:
                    if line.salary_rule_id.code != 'NET':
                        totalOther = totalOther + sso_amount + line.amount
                        # line.name = f'{line.name} {line.amount} {totalOther}'

            # Loop re calculate1
            for line in slip.line_ids:
                if line.salary_rule_id.code == 'NET':
                    workDataAmount = line.amount
                    line.amount = amonthSalary + totalOther + sso_amount
                    line.total = amonthSalary + totalOther + sso_amount

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

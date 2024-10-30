from datetime import datetime
import logging
from odoo import api, models, fields

_logger = logging.getLogger(__name__)

class HRPayslip(models.Model):
    _inherit = 'hr.payslip'

    @api.model
    def compute_sheet(self):
        super(HRPayslip, self).compute_sheet()

        for slip in self:
            loan_contracts = self.env['loan.request'].search([
                ('partner_id', '=', slip.employee_id.id)
            ])

            amonth_salary = 0
            total_other_deductions = 0
            sso_amount = 0
            withholding_tax = 0

            # Get active contract for the employee
            contract = self.env['hr.contract'].search([
                ('employee_id', '=', slip.employee_id.id),
                ('state', '=', 'open')
            ], limit=1)

            _logger.info(f"Processing payslip for employee ID: {slip.employee_id.id} | Payment Schedule: {contract.schedule_pay}")

            # Calculate workdays based on payment schedule
            workdays_count = self.calculate_workdays(slip, contract)

            for line in slip.worked_days_line_ids:
                if line.work_entry_type_id.code == 'WORK100':
                    line.number_of_days = workdays_count
                    amonth_salary = workdays_count * contract.wage
                    line.amount = amonth_salary
                elif line.work_entry_type_id.code == 'LEAVE110':
                    line.amount = 0

            for line in slip.line_ids:
                self.compute_salary_line(line, amonth_salary, loan_contracts, total_other_deductions)

            # Calculate and apply withholding tax (PND)
            withholding_tax = self.calculate_withholding_tax(amonth_salary)

            # Final net salary calculation
            for line in slip.line_ids:
                if line.salary_rule_id.code == 'NET':
                    line.amount = amonth_salary + total_other_deductions + sso_amount - withholding_tax
                    line.total = line.amount

    def calculate_workdays(self, slip, contract):
        """Calculate the number of workdays based on the employee's schedule."""
        start_date = slip.date_from
        end_date = slip.date_to
        work_entries = self.env['hr.work.entry'].search([
            ('employee_id', '=', slip.employee_id.id),
            ('date_start', '>=', start_date),
            ('date_stop', '<=', end_date)
        ], order='id ASC')

        workdays_count = 0
        week_ranges = self.get_week_ranges(start_date, end_date)

        for week in week_ranges:
            week_day_count = self.count_weekdays(week, work_entries)
            workdays_count += week_day_count

        _logger.info(f"Total workdays for employee {slip.employee_id.id}: {workdays_count}")
        return workdays_count

    def count_weekdays(self, week, work_entries):
        """Count the number of workdays in a week."""
        week_day_count = 0

        for day in week:
            duration = sum(
                entry.duration for entry in work_entries if self.is_entry_valid(entry, day)
            )
            if duration > 4:
                week_day_count += 1

        return week_day_count

    def is_entry_valid(self, entry, day):
        """Check if the work entry matches the given day."""
        if entry.date_start and entry.date_stop:
            start_date = fields.Date.from_string(entry.date_start)
            end_date = fields.Date.from_string(entry.date_stop)
            return day == start_date.strftime('%Y-%m-%d') and day == end_date.strftime('%Y-%m-%d')
        return False

    def compute_salary_line(self, line, amonth_salary, loan_contracts, total_other_deductions):
        """Compute the salary line based on the given parameters."""
        if line.salary_rule_id.code == 'BASIC':
            line.amount = amonth_salary
            line.total = amonth_salary
        elif line.salary_rule_id.code == 'GROSS':
            line.amount = amonth_salary
            line.total = amonth_salary
        elif line.salary_rule_id.code == 'SSO':
            sso_amount = amonth_salary * 0.05
            sso_amount = max(sso_amount, -750)
            line.amount = sso_amount
            line.total = sso_amount
        elif line.salary_rule_id.code == 'LOAN_DEDUCTION':
            loan = -1000
            total_other_deductions += loan
            line.amount = loan
            line.total = loan
            line.name = f'{line.name} ({loan_contracts[0].id})' if loan_contracts else line.name
        else:
            if line.salary_rule_id.code != 'NET':
                total_other_deductions += line.amount

    def calculate_withholding_tax(self, gross_salary):
        """Calculate withholding tax (PND) based on gross salary."""
        # Example tax calculation logic; adjust according to specific rules
        if gross_salary <= 15000:
            return 0  # No withholding tax for salary up to 15,000
        elif gross_salary <= 30000:
            return gross_salary * 0.05  # 5% withholding tax
        elif gross_salary <= 50000:
            return gross_salary * 0.1  # 10% withholding tax
        else:
            return gross_salary * 0.15  # 15% withholding tax
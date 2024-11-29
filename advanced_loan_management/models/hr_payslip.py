from odoo import models, fields, api
import logging
import json
from datetime import datetime, timedelta

_logger = logging.getLogger(__name__)

class HRPayslip(models.Model):
    _inherit = 'hr.payslip'

    move_type = fields.Selection([
        ('out_invoice', 'Invoice Out'),
        ('in_invoice', 'Invoice In'),
        ('slip', 'Slip')
    ], string='Move Type')

    @api.model
    def get_week_ranges(self, start_date, end_date):
        # Start from the start_date and go until the end_date
        current_date = start_date
        weeks = []
        
        while current_date <= end_date:
            # Get the start of the week (Monday)
            start_of_week = current_date - timedelta(days=current_date.weekday())
            # Create a list for the week
            week_dates = []
            
            # Generate the week dates (Monday to Sunday)
            for i in range(7):
                week_dates.append((start_of_week + timedelta(days=i)).strftime('%Y-%m-%d'))
            
            weeks.append(week_dates)
            
            # Move to the next week
            current_date = start_of_week + timedelta(days=7)
        
        return weeks
    
    def calculate_withholding_tax(self, gross_salary, empId):
        month_tax = 0
        if empId == 23: 
            month_tax = 5179.17
        elif empId == 48: 
            month_tax = 5179.17
        elif empId == 49: 
            month_tax = 5179.17
        elif empId == 46: #Fifa
            month_tax = 3679.17
        elif empId == 45: #Fifa
            month_tax = 193.33

        return month_tax
        # year_gross_salary = gross_salary * 12 
        # year_gross_salary = year_gross_salary - 100000 #หักค่าใช้จ่าย สูงสุด 100000 40(1) 50% ไม่เกิน 100000

        # year_gross_salary = year_gross_salary - 60000 #ลดหย่อนส่วนบุคคล
        # year_gross_salary = year_gross_salary - 9000 #ยกเว้นภาษีเงินได้ เงินประกันสังคมสะสม สูงสุด 9000

        # if year_gross_salary > 150000:
        #     year_gross_salary = year_gross_salary - 150000 #ยกเว้นภาษีเงินได้ 0%

        #     year_tax = year_gross_salary * 0.05
        #     month_tax = year_tax / 12
        # else:
        #     month_tax = 0

        # return month_tax
      
    
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
            totalOtherPlus = 0
            totalOther = 0
            sso_amount = 0
            withholding_tax = 0
            contract_type_code = ''

            # Get contract
            contract = self.env['hr.contract'].search([
                ('employee_id', '=', slip.employee_id.id),
                ('state', '=', 'open')  # Only get active contracts
            ], limit=1)

            if contract:
                contract_type_code = contract.contract_type_id.code
            _logger.info(f"Processing payslip for employee ID: {slip.employee_id.id} {contract.schedule_pay} {contract_type_code}")

            # Logic Calculate Work day
            if contract.schedule_pay == 'daily':
                startDate = slip.date_from  # Start date
                endDate = slip.date_to    # End date
                week_ranges = self.get_week_ranges(startDate, endDate)

                # _logger.info(f"Processing payslip for work entry: {week_ranges}")

                work_entries = self.env['hr.work.entry'].search([
                    ('employee_id', '=', slip.employee_id.id),
                    ('date_start', '>=', slip.date_from),
                    ('date_stop', '<=', slip.date_to)
                ], order='id ASC')
                workdays_count = 0
                weekIndex = 1
                for week in week_ranges:
                    weekDay = 0
                    for day in week:
                        duration = 0
                        for entry in work_entries:
                            # Calculate number of days in each work entry
                            if entry.date_start and entry.date_stop:
                                start_date = fields.Date.from_string(entry.date_start)
                                end_date = fields.Date.from_string(entry.date_stop)
                                # _logger.info(f"Processing payslip for work entry: {entry.code} {entry.duration} {entry.date_start} {entry.date_stop} || {start_date} {end_date}")
                                if day == start_date.strftime('%Y-%m-%d') and day == end_date.strftime('%Y-%m-%d'):
                                    if entry.code == 'WORK100':
                                        duration = duration + entry.duration
                                    elif entry.code == 'LEAVE110':
                                        duration = duration - entry.duration
                                    _logger.info(f"Match Entry: {entry.code} {entry.duration} {entry.date_start} {entry.date_stop} || {start_date} {end_date} - {duration}")
                                # delta_days = (end_date - start_date).days + 1  # Include both start and end dates
                                # workdays_count += delta_days 
                        if duration > 4:
                            weekDay = weekDay + 1
                    if weekDay == 6:
                        workdays_count = workdays_count + weekDay + 1
                    else:
                        workdays_count = workdays_count + weekDay
                    _logger.info(f"Week {weekIndex} : Duration {weekDay}")
                    weekIndex = weekIndex + 1

                _logger.info(f"Summary WorkDay of Emp {slip.employee_id.id} : Duration {workdays_count}")

                # for entry in work_entries:
                #     # Calculate number of days in each work entry
                #     if entry.date_start and entry.date_stop:
                #         start_date = fields.Date.from_string(entry.date_start)
                #         end_date = fields.Date.from_string(entry.date_stop)
                #         _logger.info(f"Processing payslip for work entry: {entry.code} {entry.duration} {entry.date_start} {entry.date_stop} || {start_date} {end_date}")
                #         # delta_days = (end_date - start_date).days + 1  # Include both start and end dates
                #         # workdays_count += delta_days


                # Set Workday sheet
                # scheduled_workdays_count = 0
                for line in slip.worked_days_line_ids:
                    # _logger.info(f"Processing payslip for attendance: {line} {line.number_of_days}")
                    if line.work_entry_type_id.code == 'WORK100':
                        # scheduled_workdays_count = line.number_of_days
                        # line.number_of_days = 20
                        line.number_of_days = workdays_count
                        amonthSalary = workdays_count * contract.wage #line.number_of_days * contract.wage
                        line.amount = amonthSalary
                    if line.work_entry_type_id.code == 'LEAVE110':
                        line.amount = 0
                
                for line in slip.line_ids:

                    # _logger.info(f"Processing payslip line of employee {slip.employee_id.id}: {number_of_days}")
                    if line.salary_rule_id.code == 'BASIC':
                        # loan_contracts = self.env['loan.request'].search([
                        #     ('partner_id', '=', slip.employee_id.id)
                        # ])
                        # loan_contracts_data = loan_contracts.read(['id', 'amount', 'state'])

                        # Get scheduled workdays for the employee

                        # _logger.info(f"Processing payslip for employee attendance: {scheduled_workdays_count}")

                        # workDataAmount = line.amount
                        # amonthSalary =  workDataAmount * scheduled_workdays_count
                        line.amount = amonthSalary
                        line.total = amonthSalary
                    elif line.salary_rule_id.code == 'GROSS':
                        line.amount = amonthSalary
                        line.total = amonthSalary
                    elif line.salary_rule_id.code == 'SSO':
                        if contract_type_code == 'จ่ายประกันสังคม': 
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
                        # workDataAmount = line.amount
                        line.amount = amonthSalary + totalOther + sso_amount
                        line.total = amonthSalary + totalOther + sso_amount
            elif contract.schedule_pay == 'monthly':

                startDate = slip.date_from  # Start date
                endDate = slip.date_to    # End date
                week_ranges = self.get_week_ranges(startDate, endDate)

                # _logger.info(f"Processing payslip for work entry: {week_ranges}")

                work_entries = self.env['hr.work.entry'].search([
                    ('employee_id', '=', slip.employee_id.id),
                    ('date_start', '>=', slip.date_from),
                    ('date_stop', '<=', slip.date_to)
                ], order='id ASC')
                workdays_count = 0
                weekIndex = 1
                for week in week_ranges:
                    weekDay = 0
                    for day in week:
                        duration = 0
                        for entry in work_entries:
                            # Calculate number of days in each work entry
                            if entry.date_start and entry.date_stop:
                                start_date = fields.Date.from_string(entry.date_start)
                                end_date = fields.Date.from_string(entry.date_stop)
                                # _logger.info(f"Processing payslip for work entry: {entry.code} {entry.duration} {entry.date_start} {entry.date_stop} || {start_date} {end_date}")
                                if day == start_date.strftime('%Y-%m-%d') and day == end_date.strftime('%Y-%m-%d'):
                                    if entry.code == 'WORK100':
                                        duration = duration + entry.duration
                                    elif entry.code == 'LEAVE110':
                                        duration = duration - entry.duration
                                    _logger.info(f"Match Entry: {entry.code} {entry.duration} {entry.date_start} {entry.date_stop} || {start_date} {end_date} - {duration}")
                                # delta_days = (end_date - start_date).days + 1  # Include both start and end dates
                                # workdays_count += delta_days 
                        if duration > 4:
                            weekDay = weekDay + 1
                    # if weekDay == 6:
                    #     workdays_count = workdays_count + weekDay + 1
                    # else:
                    workdays_count = workdays_count + weekDay
                    _logger.info(f"Week {weekIndex} : Duration {weekDay}")
                    weekIndex = weekIndex + 1

                _logger.info(f"Summary WorkDay of Emp {slip.employee_id.id} : Duration {workdays_count}")

                # for entry in work_entries:
                #     # Calculate number of days in each work entry
                #     if entry.date_start and entry.date_stop:
                #         start_date = fields.Date.from_string(entry.date_start)
                #         end_date = fields.Date.from_string(entry.date_stop)
                #         _logger.info(f"Processing payslip for work entry: {entry.code} {entry.duration} {entry.date_start} {entry.date_stop} || {start_date} {end_date}")
                #         # delta_days = (end_date - start_date).days + 1  # Include both start and end dates
                #         # workdays_count += delta_days


                # Set Workday sheet
                # scheduled_workdays_count = 0
                for line in slip.worked_days_line_ids:
                    # _logger.info(f"Processing payslip for attendance: {line} {line.number_of_days}")
                    if line.work_entry_type_id.code == 'WORK100':
                        # scheduled_workdays_count = line.number_of_days
                        # line.number_of_days = 20
                        line.number_of_days = workdays_count
                        amonthSalary = contract.wage #line.number_of_days * contract.wage
                        line.amount = amonthSalary
                    if line.work_entry_type_id.code == 'LEAVE110':
                        line.amount = 0
                
                withholding_tax = self.calculate_withholding_tax(amonthSalary,  slip.employee_id.id)


                for line in slip.line_ids:
                    if line.salary_rule_id.code == 'EXTRAPAID':
                        # workDataAmount = line.amount
                        _logger.info(f"Processing EXTRAPAID for employee attendance: {line.amount}")
                        totalOtherPlus = line.amount
                        line.amount = totalOtherPlus
                        line.total = totalOtherPlus

                for line in slip.line_ids:
                    if line.salary_rule_id.code == 'BASIC':
                        # loan_contracts = self.env['loan.request'].search([
                        #     ('partner_id', '=', slip.employee_id.id)
                        # ])
                        # loan_contracts_data = loan_contracts.read(['id', 'amount', 'state'])

                        # Get scheduled workdays for the employee

                        # _logger.info(f"Processing payslip for employee attendance: {scheduled_workdays_count}")

                        # workDataAmount = line.amount
                        # amonthSalary =  workDataAmount * scheduled_workdays_count
                        line.amount = amonthSalary
                        line.total = amonthSalary
                    elif line.salary_rule_id.code == 'GROSS':
                        line.amount = amonthSalary + totalOtherPlus
                        line.total = amonthSalary + totalOtherPlus
                    elif line.salary_rule_id.code == 'SSO':
                        if contract_type_code == 'จ่ายประกันสังคม': 
                            sso_amount = amonthSalary * 0.05 
                            if sso_amount > 750:
                                sso_amount = 750
                            else:
                                sso_amount = sso_amount
                            line.amount = sso_amount
                            line.total = sso_amount
                    # elif line.salary_rule_id.code == 'LOAN_DEDUCTION':
                    #     loan = -1000
                    #     totalOther = totalOther + loan
                    #     line.amount = loan
                    #     line.total = loan
                    #     line.name = f'{line.name} ({loan_contracts[0].id})'
                    #     # for loan in loan_contracts:
                        #     line.name = loan
                    else:
                        if line.salary_rule_id.code != 'NET':
                            _logger.info(f"Processing other line of employee {line.salary_rule_id.code}: {line.amount}")
                            totalOther = totalOther + sso_amount + line.amount
                            # line.name = f'{line.name} {line.amount} {totalOther}'

                _logger.info(f"Processing payslip deduct cost of employee {totalOther}: {sso_amount} {withholding_tax}")
                # Loop re calculate1
                for line in slip.line_ids:
                    if line.salary_rule_id.code == 'with_holding':
                        # workDataAmount = line.amount
                        line.amount = withholding_tax
                        line.total = withholding_tax
                    if line.salary_rule_id.code == 'NET':
                        # workDataAmount = line.amount
                        sumTotal = amonthSalary - ((-totalOther) + sso_amount + withholding_tax)
                        line.amount = sumTotal
                        line.total = sumTotal


    @api.model
    def write(self, vals):
        """
        Override the write method to listen for the state change when a payslip is paid.
        """
        # Check if the 'state' field is in the values being written
        if 'state' in vals:
            old_state = self.state
            new_state = vals['state']
            
            # If the state is changing to 'done' (or 'paid', depending on your workflow)
            message = f"Payslip {self.number} has been change status to {new_state}"
            _logger.info(message)
            if old_state != new_state and new_state == 'done':  # You can adjust to 'paid' if that's your state
                # Trigger custom logic when payslip is marked as 'Paid'
                self.trigger_custom_event()

        return super(HRPayslip, self).write(vals)

    def trigger_custom_event(self):
        """
        Custom function to trigger an event when the payslip is marked as paid.
        """
        # Example of a log message
        contract = self.env['hr.contract'].search([
                ('employee_id', '=', self.employee_id.id),
                ('state', '=', 'open')  # Only get active contracts
            ], limit=1)


        salary = 0 
        taxWithHolding = 0
        sso = 0
        for line in self.line_ids:
            if line.salary_rule_id.code == 'BASIC':
                salary = line.amount
            elif line.salary_rule_id.code == 'with_holding':
                taxWithHolding = line.amount
            elif line.salary_rule_id.code == 'SSO':
                sso = line.amount
        
        message = f"Payslip {self.number} has been marked as create draft entry. {taxWithHolding} {contract.x_studio_total_withholding}"
        _logger.info(message)

        # Test Save value
        if isinstance(contract.x_studio_total_net, str):
            try:
                total_net = float(contract.x_studio_total_net.replace(',', ''))
            except ValueError:
                total_net = 0.0
        else:
            total_net = 0.0
        contract.x_studio_total_net = str(total_net + float(salary))

        if isinstance(contract.x_studio_total_withholding, str):
            try:
                total_withholding = float(contract.x_studio_total_withholding.replace(',', ''))
            except ValueError:
                total_withholding = 0.0
        else:
            total_withholding = 0.0
        contract.x_studio_total_withholding = str(total_withholding + float(taxWithHolding))

        if isinstance(contract.x_studio_total_sso, str):
            try:
                total_sso = float(contract.x_studio_total_sso.replace(',', ''))
            except ValueError:
                total_sso = 0.0
        else:
            total_sso = 0.0
        contract.x_studio_total_sso = str(total_sso + float(sso))


        # Example of broadcasting a message via the bus system (optional)
        # Odoo bus to notify other parts of the system (or external systems)
        # Bus.sendone(self.env.cr, self.env.uid, 'custom.payslip.paid', message)

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

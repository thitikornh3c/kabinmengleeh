from odoo import models, fields, api
import logging
import json
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP

_logger = logging.getLogger(__name__)

class HRPayslip(models.Model):
    _inherit = 'hr.payslip'
    move_type = fields.Selection([
        ('out_invoice', 'Invoice Out'),
        ('in_invoice', 'Invoice In'),
        ('slip', 'Slip')
    ], string='Move Type')

    q_total_net = fields.Float(
        string='Total Net',
        compute='_compute_salary_details',
        store=False,
    )
    q_total_sso = fields.Float(
        string='Total SSO',
        compute='_compute_salary_details',
        store=False,
    )
    q_total_withholding = fields.Float(
        string='Total Withholding',
        compute='_compute_salary_details',
        store=False,
    )

    q_year = fields.Integer(
        string='Year',
        compute='_compute_salary_details',
        store=False,
    )
    q_salary = fields.Float(
        string='Salary',
        compute='_compute_salary_details',
        store=False,
    )
    q_salary_total = fields.Float(
        string='Salary Total',
        compute='_compute_salary_details',
        store=False,
    )
    q_sso = fields.Float(
        string='SSO',
        compute='_compute_salary_details',
        store=False,
    )
    q_withholding = fields.Float(
        string='WithHolding',
        compute='_compute_salary_details',
        store=False,
    )
    q_total_deduct = fields.Float(
        string='Total Deduct',
        compute='_compute_salary_details',
        store=False,
    )
    q_total_amount = fields.Float(
        string='Total Amount',
        compute='_compute_salary_details',
        store=False,
    )

    q_other = fields.Float(
        string='Unknown',
        compute='_compute_salary_details',
        store=False,
    )

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
    
    def round_half_up(self, v):
        # amount = int(n)
        # round = amount + n
        # return int(Decimal(n).to_integral_value(rounding=ROUND_HALF_UP))
        amount = int(v)
        diff = amount - v  # fractional part, will be positive for negatives

        if diff == 0.5:
            if amount % 2 == 0:
                return amount
            else:
                return amount - 1
        elif diff < 0.5:
            return amount
        else:  # diff > 0.5
            return amount - 1

    def calculate_withholding_tax(self, gross_salary, empId):
        month_tax = 0
        # if empId == 23: 
        #     month_tax = 5179.17
        # elif empId == 48: 
        #     month_tax = 5179.17
        # elif empId == 49: 
        #     month_tax = 5179.17
        # elif empId == 46: #Fifa
        #     month_tax = 3679.17
        # elif empId == 45: #Fifa
        #     month_tax = 193.33

        # return month_tax

        year_gross_salary = gross_salary * 12 
        year_gross_salary = year_gross_salary - 100000 #หักค่าใช้จ่าย สูงสุด 100000 40(1) 50% ไม่เกิน 100000

        year_gross_salary = year_gross_salary - 60000 #ลดหย่อนส่วนบุคคล
        year_gross_salary = year_gross_salary - 9000 #ยกเว้นภาษีเงินได้ เงินประกันสังคมสะสม สูงสุด 9000

        if year_gross_salary > 150000:
            year_gross_salary = year_gross_salary - 150000 #ยกเว้นภาษีเงินได้ 0%

            year_tax = year_gross_salary * 0.05
            month_tax = year_tax / 12
        else:
            month_tax = 0

        return month_tax
      
    def calculate_withholding_tax_2(self, gross_salary, empId):
        if empId == 7:
            month_tax = gross_salary * 0.03
        else:
            month_tax = 0
        # return month_tax
        
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

        return month_tax
    
    @api.model
    def compute_sheet(self):
        super(HRPayslip, self).compute_sheet()

        # validated_entries = self.env['hr.work.entry'].search([('state', '=', 'validated')])
        
        # # Revert each to draft using the proper method
        # for entry in validated_entries:
        #     entry.sudo().write({'state': 'draft'})

        # _logger.info(f"{len(validated_entries)} work entries reverted to draft.")


        for slip in self:

            year = slip.date_from.strftime('%Y')
            month = int(slip.date_from.strftime('%m'))
            loan_line = None

            loan_contracts = self.env['loan.request'].search([
                ('partner_id', '=', slip.employee_id.id) #slip.employee_id.id
                # ('state', '=', 'active')
            ], limit=1)
            
            _logger.info(f"Loan ID: {loan_contracts.id} for Employee ID: {slip.employee_id.id}")
            for repayment in loan_contracts.repayment_lines_ids:
                line_year = repayment.date.strftime('%Y')
                line_month = int(repayment.date.strftime('%m'))
                if year == line_year and month == line_month:
                    _logger.info(f"Repayment Line: ID={repayment.id}, Date={repayment.date}, Amount={repayment.amount}")
                    loan_line = repayment
               
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
            grossTotal = 0

            if loan_line:
                _logger.info(f"Using loan line ID: {loan_line.id}, amount: {loan_line.amount}")
                for line in slip.line_ids:
                    if line.salary_rule_id.code == 'BASIC_LOAN_DEDUCTION' and loan_line:
                        line_year = repayment.date.strftime('%Y')
                        line_month = int(repayment.date.strftime('%m'))
                        line.name = f"{line.name} ({line_month}/{line_year})"
    
                        loan = -loan_line.amount
                        totalOther = totalOther + loan
                        line.amount = loan
                        line.total = loan  

            # Get contract
            contract = self.env['hr.contract'].search([
                ('employee_id', '=', slip.employee_id.id),
                ('state', '=', 'open')  # Only get active contracts
            ], limit=1)

            if contract:
                contract_type_code = contract.contract_type_id.code
            _logger.info(f"Processing payslip for employee ID: {slip.employee_id.id} {contract.schedule_pay} {contract_type_code}")

          
                # slip.show_loan = True
            # else:
                # slip.show_loan = False

            # Logic Calculate Work day
            if contract.schedule_pay == 'daily':
                startDate = slip.date_from  # Start date
                endDate = slip.date_to    # End date
                week_ranges = self.get_week_ranges(startDate, endDate)

                # Calculate difference in days (inclusive)
                number_of_days = (endDate - startDate).days + 1

                _logger.info(f"Processing1 payslip total days: {number_of_days}")

                work_entries = self.env['hr.work.entry'].search([
                    ('employee_id', '=', slip.employee_id.id),
                    ('date_start', '>=', slip.date_from),
                    ('date_stop', '<=', slip.date_to)
                ], order='id ASC')
                workdays_count = number_of_days
                weekIndex = 1
                leave90 = 0
                leave100 = 0
                leave105 = 0
                leave110 = 0
                leave120 = 0
                weekBonus = 0
                for week in week_ranges:
                    isWeekLeave = False
                    for day in week:
                        for entry in work_entries:
                            if entry.date_start and entry.date_stop:
                                start_date = fields.Date.from_string(entry.date_start)
                                end_date = fields.Date.from_string(entry.date_stop)
                                if day == start_date.strftime('%Y-%m-%d') and day == end_date.strftime('%Y-%m-%d'):
                                    if (start_date.strftime('%a').upper() == 'MON' or start_date.strftime('%a').upper() == 'SAT') and entry.code != 'WORK100':
                                        isWeekLeave = True
                                        
                                    if entry.code == 'LEAVE90': #Unpaid
                                        leave90 = leave90 + 0.5 #entry.duration
                                    elif entry.code == 'LEAVE100': #Generic
                                        leave100 = leave100 + 0.5#entry.duration
                                    elif entry.code == 'LEAVE105': #Compensatory
                                        leave105 = leave105 + 0.5#entry.duration
                                    elif entry.code == 'LEAVE110': #Sick Time Off
                                        leave110 = leave110 + 0.5#entry.duration
                                    elif entry.code == 'LEAVE120': #Paid Time Off
                                        leave120 = leave120 + 0.5#entry.duration
                    if isWeekLeave == True:
                        weekBonus = weekBonus + 1
                                        
                # for week in week_ranges:
                #     weekDay = 0
                #     for day in week:
                #         duration = 0
                #         for entry in work_entries:
                #             # Calculate number of days in each work entry
                #             if entry.date_start and entry.date_stop:
                #                 start_date = fields.Date.from_string(entry.date_start)
                #                 end_date = fields.Date.from_string(entry.date_stop)
                #                 weekLeave = False
                #                 # _logger.info(f"Processing payslip for work entry: {entry.code} {entry.duration} {entry.date_start} {entry.date_stop} || {start_date} {end_date}")
                #                 if day == start_date.strftime('%Y-%m-%d') and day == end_date.strftime('%Y-%m-%d'):
                #                     if (start_date.strftime('%a').upper() == 'MON' or start_date.strftime('%a').upper() == 'SAT') and entry.code != 'WORK100':
                #                         weekLeave = True
                                        
                #                     if entry.code == 'WORK100':
                #                         duration = duration + 0.5#entry.duration
                #                     elif entry.code == 'LEAVE90':
                #                         leave90 = leave90 - 0.5#entry.duration
                #                     elif entry.code == 'LEAVE100':
                #                         leave100 = leave100 - 0.5#entry.duration
                #                     elif entry.code == 'LEAVE105':
                #                         leave105 = leave105 - 0.5#entry.duration
                #                     elif entry.code == 'LEAVE110':
                #                         leave110 = leave110 - 0.5#entry.duration
                #                     elif entry.code == 'LEAVE120':
                #                         leave120 = leave120 - 0.5#entry.duration
                                        
                #                     _logger.info(f"Match Entry: {start_date.strftime('%a').upper()} {entry.code} {entry.duration} {entry.date_start} {entry.date_stop} || {start_date} {end_date} - {duration}")
                #                 # delta_days = (end_date - start_date).days + 1  # Include both start and end dates
                #                 # workdays_count += delta_days 
                #         weekDay = weekDay + duration
                #         _logger.info(f"Summary Entry: {day} {duration}")
                #         # if weekLeave != False:
                #     if weekDay > 4 and weekLeave == False:
                #         weekDay =  weekDay + 1
                #     workdays_count = workdays_count + weekDay
                #     _logger.info(f"Week {weekIndex} : Duration {weekDay}")
                #     weekIndex = weekIndex + 1
                workdays_count = workdays_count - leave90
                workdays_count = workdays_count - weekBonus

                _logger.info(f"Summary WorkDay of Emp {slip.employee_id.id} : Day work {workdays_count}, WeekBonus -{weekBonus} Unpaid {leave90}, Generic {leave100}, Compensatory {leave105}, Sick {leave110}, Paid {leave120}")


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
                    if line.work_entry_type_id.code == 'LEAVE90':
                        line.number_of_days = abs(leave90)
                    if line.work_entry_type_id.code == 'LEAVE100':
                        line.number_of_days = abs(leave100)
                        line.amount = contract.wage
                    if line.work_entry_type_id.code == 'LEAVE105':
                        line.number_of_days = abs(leave105)
                        line.amount = contract.wage
                    if line.work_entry_type_id.code == 'LEAVE110':
                        line.number_of_days = abs(leave110)
                    if line.work_entry_type_id.code == 'LEAVE120':
                        line.number_of_days = abs(leave120)

                basic_amount = 0
                for line in slip.line_ids:
                    if line.salary_rule_id.code == 'BASIC':
                        basic_amount = line.amount
                #         else: 
                #             line.amount = amonthSalary 
                #             line.total = amonthSalary

                # for line in slip.line_ids:
                #     if line.salary_rule_id.code == 'EXTRAPAID':
                #         _logger.info(f"Processing EXTRAPAID for employee attendance: {line.amount}")
                #         totalOtherPlus = line.amount
                #         line.amount = totalOtherPlus
                #         line.total = totalOtherPlus


                for line in slip.line_ids:
                    # if line.salary_rule_id.code == 'GROSS':
                    #     line.amount = amonthSalary + totalOtherPlus
                    #     line.total = amonthSalary + totalOtherPlus
                    if line.salary_rule_id.code == 'SSO':
                        if contract_type_code == 'จ่ายประกันสังคม': 
                            sso_amount = basic_amount * 0.05 
                            if sso_amount > 750:
                                sso_amount = -750
                            else:
                                sso_amount = -sso_amount

                            sso_amount = self.round_half_up(sso_amount)
                            line.amount = sso_amount
                            line.total = sso_amount
                    # elif line.salary_rule_id.code == 'BASIC_LOAN_DEDUCTION' and loan_line:
                    #     line_year = repayment.date.strftime('%Y')
                    #     line_month = int(repayment.date.strftime('%m'))
                    #     line.name = f"{line.name} ({line_month}/{line_year})"
    
                    #     loan = -loan_line.amount
                    #     totalOther = totalOther + loan
                    #     line.amount = loan
                    #     line.total = loan
                        # line.name = f'{line.name} ({loan_contracts[0].id})'
                    
                        # for loan in loan_contracts:
                        #     line.name = loan
                    # else:
                    #     if line.salary_rule_id.code != 'EXTRAPAID':
                    #         totalOther = totalOther + line.amount
                    #        # line.name = f'{line.name} {line.amount} {totalOther}'

                # Loop re calculate1
                # for line in slip.line_ids:
                if line.salary_rule_id.code == 'NET':
                    # workDataAmount = line.amount
                    _logger.info(f"Processing NET line of employee {line.amount } {sso_amount} {line.salary_rule_id}")
                    netSum = line.amount + sso_amount + totalOther
                    line.amount = netSum
                    line.total = netSum
                    # line.amount = amonthSalary + totalOther + sso_amount
                    # line.total = amonthSalary + totalOther + sso_amount
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

                leave90 = 0
                leave100 = 0
                leave105 = 0
                leave110 = 0
                leave120 = 0
                weekDay = 0

                for week in week_ranges:
                    for day in week:
                        for entry in work_entries:
                            if entry.date_start and entry.date_stop:
                                start_date = fields.Date.from_string(entry.date_start)
                                end_date = fields.Date.from_string(entry.date_stop)
                                if day == start_date.strftime('%Y-%m-%d') and day == end_date.strftime('%Y-%m-%d'):
                                    if entry.code == 'WORK100':
                                        weekDay = weekDay + 0.5
                                        
                                    if entry.code == 'LEAVE90': #Unpaid
                                        leave90 = leave90 + 0.5 #entry.duration
                                    elif entry.code == 'LEAVE100': #Generic
                                        leave100 = leave100 + 0.5#entry.duration
                                    elif entry.code == 'LEAVE105': #Compensatory
                                        leave105 = leave105 + 0.5#entry.duration
                                    elif entry.code == 'LEAVE110': #Sick Time Off
                                        leave110 = leave110 + 0.5#entry.duration
                                    elif entry.code == 'LEAVE120': #Paid Time Off
                                        leave120 = leave120 + 0.5#entry.duration
                # for week in week_ranges:
                #     weekDay = 0
                #     for day in week:
                #         duration = 0
                #         for entry in work_entries:
                #             # Calculate number of days in each work entry
                #             if entry.date_start and entry.date_stop:
                #                 start_date = fields.Date.from_string(entry.date_start)
                #                 end_date = fields.Date.from_string(entry.date_stop)
                #                 # _logger.info(f"Processing payslip for work entry: {entry.code} {entry.duration} {entry.date_start} {entry.date_stop} || {start_date} {end_date}")
                #                 if day == start_date.strftime('%Y-%m-%d') and day == end_date.strftime('%Y-%m-%d'):
                #                     if entry.code == 'WORK100':
                #                         duration = duration + entry.duration
                #                     elif entry.code == 'LEAVE110':
                #                         duration = duration - entry.duration
                #                     _logger.info(f"Match Entry: {entry.code} {entry.duration} {entry.date_start} {entry.date_stop} || {start_date} {end_date} - {duration}")
                #                 # delta_days = (end_date - start_date).days + 1  # Include both start and end dates
                #                 # workdays_count += delta_days 
                #         if duration > 4:
                #             weekDay = weekDay + 1
                #     # if weekDay == 6:
                #     #     workdays_count = workdays_count + weekDay + 1
                #     # else:
                    _logger.info(f"Week {weekIndex} : Duration {weekDay}")
                    weekIndex = weekIndex + 1
                workdays_count = weekDay
                # _logger.info(f"Summary WorkDay of Emp {slip.employee_id.id} : Duration {workdays_count}")
                _logger.info(f"Summary WorkDay of Emp {slip.employee_id.id} : Day work {workdays_count}, Unpaid {leave90}, Generic {leave100}, Compensatory {leave105}, Sick {leave110}, Paid {leave120}")

                # for entry in work_entries:
                #     # Calculate number of days in each work entry
                #     if entry.date_start and entry.date_stop:
                #         start_date = fields.Date.from_string(entry.date_start)
                #         end_date = fields.Date.from_string(entry.date_stop)
                #         _logger.info(f"Processing payslip for work entry: {entry.code} {entry.duration} {entry.date_start} {entry.date_stop} || {start_date} {end_date}")
                #         # delta_days = (end_date - start_date).days + 1  # Include both start and end dates
                #         # workdays_count += delta_days

                basic_amount = 0
                for line in slip.line_ids:
                    if line.salary_rule_id.code == 'BASIC':
                        basic_amount = line.amount

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
                    if line.work_entry_type_id.code == 'LEAVE120':
                        line.amount = 0
                    if line.work_entry_type_id.code == 'LEAVE100':
                        line.amount = 0
                    if line.work_entry_type_id.code == 'LEAVE105':
                        line.amount = 0

                    if line.work_entry_type_id.code == 'LEAVE90':
                        line.number_of_days = abs(leave90)
                    if line.work_entry_type_id.code == 'LEAVE100':
                        line.number_of_days = abs(leave100)
                    if line.work_entry_type_id.code == 'LEAVE105':
                        line.number_of_days = abs(leave105)
                    if line.work_entry_type_id.code == 'LEAVE110':
                        line.number_of_days = abs(leave110)
                    if line.work_entry_type_id.code == 'LEAVE120':
                        line.number_of_days = abs(leave120)
                
                if slip.company_id.id == 1:
                    withholding_tax = self.calculate_withholding_tax_2(amonthSalary,  slip.employee_id.id)
                else:
                    withholding_tax = self.calculate_withholding_tax(amonthSalary,  slip.employee_id.id)


                for line in slip.line_ids:
                    if line.salary_rule_id.code == 'EXTRAPAID':
                        # workDataAmount = line.amount
                        _logger.info(f"Processing EXTRAPAID for employee attendance: {line.amount}")
                        totalOtherPlus = line.amount
                        line.amount = totalOtherPlus
                        line.total = totalOtherPlus

                for line in slip.line_ids:
                    # if line.salary_rule_id.code == 'BASIC':
                    #     # loan_contracts = self.env['loan.request'].search([
                    #     #     ('partner_id', '=', slip.employee_id.id)
                    #     # ])
                    #     # loan_contracts_data = loan_contracts.read(['id', 'amount', 'state'])

                    #     # Get scheduled workdays for the employee

                    #     # _logger.info(f"Processing payslip for employee attendance: {scheduled_workdays_count}")

                    #     # workDataAmount = line.amount
                    #     # amonthSalary =  workDataAmount * scheduled_workdays_count
                    #     line.amount = amonthSalary
                    #     line.total = amonthSalary
                    # elif line.salary_rule_id.code == 'GROSS':
                    #     line.amount = amonthSalary + totalOtherPlus
                    #     line.total = amonthSalary + totalOtherPlus
                    if line.salary_rule_id.code == 'SSO':
                        if contract_type_code == 'จ่ายประกันสังคม': 
                            sso_amount = basic_amount * 0.05 
                            if sso_amount > 750:
                                sso_amount = -750
                            else:
                                sso_amount = -sso_amount
                            
                            sso_amount = self.round_half_up(sso_amount)
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
                    # else:
                    #     if line.salary_rule_id.code != 'NET':
                    #         _logger.info(f"Processing other line of employee {line.salary_rule_id.code}: {line.amount}")
                    #         totalOther = totalOther + sso_amount + line.amount
                    #         # line.name = f'{line.name} {line.amount} {totalOther}'

                _logger.info(f"Processing payslip deduct cost of employee {totalOther}: {sso_amount} {withholding_tax}")
                # Loop re calculate1
                for line in slip.line_ids:
                    if line.salary_rule_id.code == 'with_holding':
                        # workDataAmount = line.amount
                        line.amount = -withholding_tax
                        line.total = -withholding_tax
                    if line.salary_rule_id.code == 'NET':
                        # workDataAmount = line.amount
                        
                        sumTotal = line.amount + sso_amount - withholding_tax + totalOther
                        # sumTotal = amonthSalary - ((-totalOther) + sso_amount + withholding_tax)
                        line.amount = sumTotal
                        line.total = sumTotal
                        
            slip.trigger_custom_event()
                        # if slip.employee_id.id == 50:
                        #     line.amount = 12500
                        #     line.total = 12500


    @api.model
    def write(self, vals):
        """
        Override the write method to listen for the state change when a payslip is paid.
        """
        # Check if the 'state' field is in the values being written
        if 'state' in vals:
            for payslip in self:
                old_state = payslip.state
                new_state = vals['state']
                
                # If the state is changing to 'done' (or 'paid', depending on your workflow)
                message = f"Payslip {payslip.number} has been change status to {new_state}"
                _logger.info(message)
                if old_state != new_state and new_state == 'done':  # You can adjust to 'paid' if that's your state
                    # Trigger custom logic when payslip is marked as 'Paid'
                    payslip.trigger_custom_event()
                if new_state == 'verify': 
                    payslip.trigger_custom_event()

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
        net = 0

        x_studio_total_net = 0
        x_studio_total_withholding = 0
        x_studio_total_sso = 0

        year = self.date_from.strftime('%Y')
        month = int(self.date_from.strftime('%m'))
        
        _logger.info(f"Payslip1111111 {self.number} line_ids: {self.line_ids} {self.company_id.id}")
        for line in self.line_ids:
            if line.salary_rule_id.code == 'BASIC':
                salary = line.amount
            elif line.salary_rule_id.code == 'with_holding':
                taxWithHolding = line.amount
            elif line.salary_rule_id.code == 'SSO':
                sso = line.amount
            elif line.salary_rule_id.code == 'NET':
                net = line.amount

        # message = f"Payslip {self.number} has been marked as create draft entry. {taxWithHolding} {contract.x_studio_total_withholding}"
        # _logger.info(message)

       


        other_deduct = 0.0
        for line in self.line_ids:
            if line.salary_rule_id.code == 'BASIC_LOAN_DEDUCTION':
                other_deduct = other_deduct + float(line.amount)
            if line.salary_rule_id.code == 'DEDUCTION':
                other_deduct = other_deduct + float(line.amount)

        other_paid = 0.0
        for line in self.line_ids:
            if 'EXTRAPAID' in line.salary_rule_id.code:
                other_paid += float(line.amount)

        amonthSalary = float(salary) + other_paid

        _logger.info(f"salary: {salary} otherPaid: {other_paid} taxWithHolding: {taxWithHolding} sso: {sso} net: {net}")

        # Find Slip Last month of this Employee
        if month == 1:
            x_studio_total_net = 0
            x_studio_total_withholding = 0
            x_studio_total_sso = 0

            _logger.info(f"New Year {salary} {taxWithHolding} {sso}")

            if self.company_id.id == 1:
                x_studio_total_net = str(float(amonthSalary))
            else:
                x_studio_total_net = str(float(salary))
                
            x_studio_total_withholding = str(abs(float(taxWithHolding)))
            x_studio_total_sso = str(abs(float(sso)))
        else:
            slipLastMonth = self.env['x_employee_salaries'].search([
                    ('x_studio_employee', '=', self.employee_id.id),
                    ('x_studio_year', '=', year),
                    ('x_studio_month', '=', month - 1),
                    # ('x_studio_slip', '=', self.id),
                ], limit=1)
            
            if slipLastMonth:
                # Test Save value
                _logger.info(f"Use Last Month Data to make Total accumarative")
                if isinstance(slipLastMonth.x_studio_total_salary, str):
                    try:
                        total_net = float(slipLastMonth.x_studio_total_salary.replace(',', ''))
                    except ValueError:
                        total_net = 0.0
                else:
                    total_net = 0.0

                if self.company_id.id == 1:
                    x_studio_total_net = str(total_net + float(amonthSalary))
                else:
                    x_studio_total_net = str(total_net + float(salary))
                    
                

                if isinstance(slipLastMonth.x_studio_total_withholding, str):
                    try:
                        total_withholding = float(slipLastMonth.x_studio_total_withholding.replace(',', ''))
                    except ValueError:
                        total_withholding = 0.0
                else:
                    total_withholding = 0.0
                x_studio_total_withholding = str(total_withholding + abs(float(taxWithHolding)))

                if isinstance(slipLastMonth.x_studio_total_sso, str):
                    try:
                        total_sso = float(slipLastMonth.x_studio_total_sso.replace(',', ''))
                    except ValueError:
                        total_sso = 0.0
                else:
                    total_sso = 0.0
                x_studio_total_sso = str(total_sso + abs(float(sso)))
            else:
                # Use Snapshot Data in Contract
                _logger.info(f"Not Found Old Slip Logs {salary} {taxWithHolding} {sso}")
                if isinstance(contract.x_studio_total_net, str):
                    try:
                        total_net = float(contract.x_studio_total_net.replace(',', ''))
                    except ValueError:
                        total_net = 0.0
                else:
                    total_net = 0.0

                if self.company_id.id == 1:
                    x_studio_total_net = str(total_net + float(amonthSalary))
                else:
                    x_studio_total_net = str(total_net + float(salary))
                

                if isinstance(contract.x_studio_total_withholding, str):
                    try:
                        total_withholding = float(contract.x_studio_total_withholding.replace(',', ''))
                    except ValueError:
                        total_withholding = 0.0
                else:
                    total_withholding = 0.0
                x_studio_total_withholding = str(total_withholding + abs(float(taxWithHolding)))

                if isinstance(contract.x_studio_total_sso, str):
                    try:
                        total_sso = float(contract.x_studio_total_sso.replace(',', ''))
                    except ValueError:
                        total_sso = 0.0
                else:
                    total_sso = 0.0
                x_studio_total_sso = str(total_sso + abs(float(sso)))


        empSlipLog = self.env['x_employee_salaries'].search([
                ('x_studio_slip', '=', self.id),
            ], limit=1)

        
        
        if empSlipLog:
            # Update
            empSlipLog.x_studio_total_salary = x_studio_total_net
            empSlipLog.x_studio_total_sso = x_studio_total_sso
            empSlipLog.x_studio_total_withholding = x_studio_total_withholding
            empSlipLog.x_studio_salary = salary
            empSlipLog.x_studio_sso = str(abs(float(sso)))
            empSlipLog.x_studio_with_holding = str(abs(float(taxWithHolding)))
            empSlipLog.x_studio_total_amount = net
            empSlipLog.x_studio_extrapaid = other_paid 
            empSlipLog.x_studio_deduction = str(abs(float(other_deduct or 0.0)))
        else:
             self.env['x_employee_salaries'].create({
                'x_name': str(year) + str(month),
                'x_studio_employee': self.employee_id.id,
                'x_studio_slip': self.id,
                'x_studio_year': year,
                'x_studio_month': month,
                'x_studio_total_salary': x_studio_total_net,
                'x_studio_total_sso': x_studio_total_sso,
                'x_studio_total_withholding': x_studio_total_withholding,

                'x_studio_salary': salary,
                'x_studio_sso': sso,
                'x_studio_with_holding': taxWithHolding,
                'x_studio_total_amount': net,
                'x_studio_extrapaid': other_paid,
                'x_studio_deduction': str(abs(float(other_deduct or 0.0)))
            })

    @api.model
    def _compute_salary_details(self):
        for payslip in self:
            # Search for the associated x_employee_salaries record
            emp_salary = self.env['x_employee_salaries'].search([
                ('x_studio_slip', '=', payslip.id),
            ], limit=1)

            # other_deduct = 0.0
            # for line in payslip.line_ids:
            #     if line.salary_rule_id.code == 'BASIC_LOAN_DEDUCTION':
            #         other_deduct = other_deduct + float(line.amount)
            #     if line.salary_rule_id.code == 'DEDUCTION':
            #         other_deduct = other_deduct + float(line.amount)

            # basic_extrapaid = 0.0
            # for line in payslip.line_ids:
            #     if line.salary_rule_id.code == 'BASIC_EXTRAPAID':
            #         basic_extrapaid += float(line.amount)
            
            if emp_salary:
                payslip.q_total_net = emp_salary.x_studio_total_salary
                payslip.q_total_sso = emp_salary.x_studio_total_sso
                payslip.q_total_withholding = emp_salary.x_studio_total_withholding
                payslip.q_year = emp_salary.x_studio_year

                payslip.q_salary = float(emp_salary.x_studio_salary or 0.0)
                payslip.q_salary_total = float(emp_salary.x_studio_salary or 0.0) + float(emp_salary.x_studio_extrapaid or 0.0)
                payslip.q_sso = emp_salary.x_studio_sso
                payslip.q_withholding = emp_salary.x_studio_with_holding

                deduction = float(emp_salary.x_studio_deduction or 0.0)
                with_holding = float(emp_salary.x_studio_with_holding or 0.0)
                sso = float(emp_salary.x_studio_sso or 0.0)

                # ถ้า deduction หรืo sso < 0 ให้คูณ -1 เพื่อแปลงเป็นบวก
                if deduction < 0:
                    deduction *= -1
                if sso < 0:
                    sso *= -1

                payslip.q_total_deduct = deduction + with_holding + sso
                # payslip.q_total_deduct = float(-emp_salary.x_studio_deduction or 0.0) + float(emp_salary.x_studio_with_holding or 0.0) + float(emp_salary.x_studio_sso or 0.0)

                payslip.q_total_amount = emp_salary.x_studio_total_amount
            else:
                payslip.q_total_net = 0.0
                payslip.q_total_sso = 0.0
                payslip.q_total_withholding = 0.0
                payslip.q_year = 0
                payslip.q_salary = 0.0
                payslip.q_sso = 0.0
                payslip.q_withholding = 0.0
                payslip.q_total_deduct = 0.0
                payslip.q_total_amount = 0.0
            
            payslip.q_other = 0.0
            payslip.trigger_custom_event()
       

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
    @api.model
    def create(self, vals):
        # Override create method to automatically add loan deduction rule
        res = super(HRPayslip, self).create(vals)
        if res:
            # Compute loan deductions and create corresponding salary lines
            _logger.info(f'Create Slip ${res.employee_id.id}')
            res.compute_sheet()
        return res

    def compute_loan_deductions(self):
        for slip in self:
            # Fetch active loan contracts for the employee
            _logger.info(f'Create Slip ${slip.employee_id.id}')
            year = self.date_from.strftime('%Y')
            month = int(self.date_from.strftime('%m'))
            
            loan_contracts = self.env['loan.request'].search([
                ('partner_id', '=', slip.employee_id.id) #slip.employee_id.id
                # ('state', '=', 'active')
            ], limit=1)
            
            _logger.info(f"Loan ID: {loan_contracts.id} for Employee ID: {slip.employee_id.id}")
            for repayment in loan_contracts.repayment_lines_ids:
                line_year = repayment.date.strftime('%Y')
                line_month = int(repayment.date.strftime('%m'))
                if year == line_year and month == line_month:
                    _logger.info(f"Repayment Line: ID={repayment.id}, Date={repayment.date}, Amount={repayment.amount}")
                    loan_line = repayment
                
            if loan_line:
                _logger.info(f"Using loan line ID: {loan_line.id}, amount: {loan_line.amount}")
                self.env['hr.payslip.line'].create({
                    'slip_id': slip.id,
                    'contract_id': slip.contract_id.id,
                    'salary_rule_id': 40,
                    'amount': repayment.amount,
                    'sequence': 197,  # Adjust sequence if needed
                    'name': 'เบิกเงินล่วงหน้า'
                })

            # for loan in loan_contracts:
            #     # Example: Deduct 10% of the loan amount
            #     deduction_amount = loan.total_amount
            #     _logger.info(loan)
            #     _logger.info(f"Not Found Old Slip Logs {loan}")
            #     # Add deduction as a salary line
            #     self.env['hr.payslip.line'].create({
            #         'payslip_id': slip.id,
            #         'salary_rule_id': 40,
            #         'amount': -deduction_amount,
            #         'sequence': 10,  # Adjust sequence if needed
            #     })
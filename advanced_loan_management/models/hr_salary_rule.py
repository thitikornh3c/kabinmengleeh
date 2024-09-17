from odoo import models, fields, api

class HRSalaryRule(models.Model):
    _inherit = 'hr.salary.rule'

    @api.model
    def get_rule_amount(self, rule, contract, date_from, date_to, payslip):
        amount = super(HRSalaryRule, self).get_rule_amount(rule, contract, date_from, date_to, payslip)
        # Add custom logic for deduction based on payment date
        if rule.code == 'LOAN_DEDUCTION':
            # if payslip.date_to < fields.Date.from_string('2024-09-01'):  # Example condition
            amount = -500  # Example deduction amount
        return amount

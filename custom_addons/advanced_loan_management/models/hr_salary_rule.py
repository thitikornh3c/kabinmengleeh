from odoo import models, fields, api

class HrSalaryRule(models.Model):
    _inherit = 'hr.salary.rule'

    @api.model
    def compute_rule(self, contract, structure_type, date_from, date_to, worked_days_line_ids, contract_id):
        return super().compute_rule(
            contract, structure_type, date_from, date_to, worked_days_line_ids, contract_id
        )

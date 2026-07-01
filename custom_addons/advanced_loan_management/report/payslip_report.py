# -*- coding: utf-8 -*-
from odoo import api, models


class ReportPayslip(models.AbstractModel):
    _name = 'report.advanced_loan_management.report_payslip_document'
    _description = 'Payslip PDF Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        payslips = self.env['hr.payslip'].browse(docids)
        return {
            'doc_ids': docids,
            'doc_model': 'hr.payslip',
            'docs': payslips,
            'data': data,
        }

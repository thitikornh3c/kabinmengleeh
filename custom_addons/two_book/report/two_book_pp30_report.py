# -*- coding: utf-8 -*-
from odoo import api, models

from .two_book_pp30_pdf import TwoBookPP30PdfBuilder


class IrActionsReport(models.Model):
    _inherit = 'ir.actions.report'

    def _render_qweb_pdf(self, report_ref, res_ids=None, data=None):
        report = self._get_report(report_ref)
        if report.report_name == 'two_book.two_book_pp30_template':
            wizard = self.env['two.book.pp30.wizard'].browse(res_ids).exists()
            if wizard:
                report_data = (data or {}).get('report_data') or wizard._prepare_report_data()
                pdf_content = TwoBookPP30PdfBuilder.build(report_data)
                return pdf_content, 'pdf'
        return super()._render_qweb_pdf(report_ref, res_ids=res_ids, data=data)


class TwoBookPP30Report(models.AbstractModel):
    _name = 'report.two_book.two_book_pp30_template'
    _description = 'Two Book PP30 VAT Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        data = data or {}
        report_data = dict(data.get('report_data') or {})
        if not report_data and docids:
            wizard = self.env['two.book.pp30.wizard'].browse(docids).exists()
            if wizard:
                report_data = wizard._prepare_report_data()
        return {
            'doc_ids': docids,
            'doc_model': 'two.book.pp30.wizard',
            'docs': self.env['two.book.pp30.wizard'].browse(docids).exists(),
            **report_data,
        }

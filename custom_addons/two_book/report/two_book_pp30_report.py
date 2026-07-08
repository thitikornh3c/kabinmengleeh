# -*- coding: utf-8 -*-
import io
from collections import OrderedDict

from odoo import api, models

from .two_book_pp30_pdf import TwoBookPP30PdfBuilder


class IrActionsReport(models.Model):
    _inherit = 'ir.actions.report'

    def _render_qweb_pdf_prepare_streams(self, report_ref, data, res_ids=None):
        report = self._get_report(report_ref)
        if report.report_name != 'two_book.two_book_pp30_template':
            return super()._render_qweb_pdf_prepare_streams(report_ref, data, res_ids=res_ids)

        if not res_ids:
            return super()._render_qweb_pdf_prepare_streams(report_ref, data, res_ids=res_ids)

        collected_streams = OrderedDict()
        report_data = (data or {}).get('report_data')
        for res_id in res_ids:
            wizard = self.env['two.book.pp30.wizard'].browse(res_id).exists()
            if not wizard:
                continue
            payload = report_data or wizard._prepare_report_data()
            pdf_bytes = TwoBookPP30PdfBuilder.build(payload)
            collected_streams[res_id] = {
                'stream': io.BytesIO(pdf_bytes),
                'attachment': None,
            }
        if collected_streams:
            return collected_streams
        return super()._render_qweb_pdf_prepare_streams(report_ref, data, res_ids=res_ids)


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

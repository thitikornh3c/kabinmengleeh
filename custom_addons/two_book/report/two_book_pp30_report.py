# -*- coding: utf-8 -*-
from odoo import api, models


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

from odoo import api, models


class PosSummaryReport(models.AbstractModel):
    _name = 'report.pos_sale_summary_report.summary_template'
    _description = 'POS Summary Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        data = data or {}
        report_data = data.get('report_data')
        if not report_data:
            wizard = self.env['pos.summary.wizard'].browse(docids)
            if wizard:
                report_data = wizard._prepare_report_data()
            else:
                report_data = {}

        wizard = self.env['pos.summary.wizard'].browse(docids)
        return {
            'doc_ids': docids,
            'doc_model': 'pos.summary.wizard',
            'docs': wizard,
            **report_data,
        }

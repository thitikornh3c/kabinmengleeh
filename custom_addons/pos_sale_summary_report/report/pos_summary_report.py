from odoo import api, models


class PosSummaryReport(models.AbstractModel):
    _name = 'report.pos_sale_summary_report.summary_template'
    _description = 'POS Summary Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        data = data or {}
        report_data = dict(data.get('report_data') or {})

        if not report_data and docids:
            wizard = self.env['pos.summary.wizard'].browse(docids).exists()
            if wizard:
                report_data = wizard._prepare_report_data()

        summary_by_date = report_data.get('summary_by_date') or {}
        report_data['summary_by_date_list'] = [
            {'date': day, 'lines': lines}
            for day, lines in sorted(summary_by_date.items())
        ]

        return {
            'doc_ids': docids,
            'doc_model': 'pos.summary.wizard',
            'docs': self.env['pos.summary.wizard'].browse(docids).exists(),
            **report_data,
        }

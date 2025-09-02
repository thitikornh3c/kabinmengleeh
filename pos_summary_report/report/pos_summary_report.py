from odoo import models, api
from collections import defaultdict
from datetime import datetime

class PosSummaryReport(models.AbstractModel):
    _name = 'report.pos_summary_report.summary_template'
    _description = 'POS Summary Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        domain = [('state', '=', 'paid')]
        if data:
            date_from = data.get('date_from')
            date_to = data.get('date_to')
            if date_from and date_to:
                domain += [('date_order', '>=', date_from), ('date_order', '<=', date_to)]
            config_ids = data.get('config_ids')
            if config_ids:
                domain += [('config_id', 'in', config_ids)]

        orders = self.env['pos.order'].search(domain)

        summary = defaultdict(lambda: {'qty': 0, 'total': 0})
        not_invoiced = []

        for order in orders:
            if not order.account_move:
                not_invoiced.append(order.name)
            for line in order.lines:
                summary[line.product_id.name]['qty'] += line.qty
                summary[line.product_id.name]['total'] += line.price_subtotal_incl

        return {
            'date_from': data.get('date_from'),
            'date_to': data.get('date_to'),
            'summary': summary,
            'not_invoiced': not_invoiced,
        }
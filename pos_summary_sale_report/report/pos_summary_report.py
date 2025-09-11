from odoo import models
from collections import defaultdict

class POSSummaryReport(models.AbstractModel):
    _name = "report.pos_daily_summary.report_pos_summary_template"
    _description = "POS Daily Summary Report"

    def _get_report_values(self, docids, data=None):
        orders = self.env['pos.order'].browse(docids)
        currency = self.env.company.currency_id

        grouped = defaultdict(lambda: {'products': [], 'total': 0, 'qty': 0})
        for order in orders:
            day = order.date_order.strftime('%d-%m-%Y')
            for line in order.lines:
                grouped[day]['products'].append({
                    'product_name': line.product_id.display_name,
                    'quantity': line.qty,
                    'price': line.price_unit,
                    'total': line.price_subtotal_incl,
                })
                grouped[day]['qty'] += line.qty
                grouped[day]['total'] += line.price_subtotal_incl

        invoiced_orders = orders.filtered(lambda o: o.invoice_status == 'invoiced')
        not_invoiced_orders = orders.filtered(lambda o: o.invoice_status != 'invoiced')

        return {
            'doc_ids': docids,
            'doc_model': 'pos.order',
            'docs': orders,
            'grouped_sales': grouped,
            'currency': currency,
            'invoiced_orders': invoiced_orders,
            'not_invoiced_orders': not_invoiced_orders,
        }

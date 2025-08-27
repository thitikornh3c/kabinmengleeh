from odoo import models, api
from collections import defaultdict
from datetime import datetime

class PosSummaryReport(models.AbstractModel):
    _name = 'report.pos_summary_report2.summary_template'
    _description = 'POS Sales Summary Report (Styled)'

    @api.model
    def _get_report_values(self, docids, data=None):
        date_from = data.get('date_from')
        date_to = data.get('date_to')
        config_ids = data.get('config_ids') or []
        dt_from = datetime.strptime(date_from, "%Y-%m-%d %H:%M:%S") if date_from else None
        dt_to = datetime.strptime(date_to, "%Y-%m-%d %H:%M:%S") if date_to else None

        domain = [('state', 'in', ['paid', 'done', 'invoiced'])]
        if dt_from:
            domain.append(('date_order', '>=', dt_from))
        if dt_to:
            domain.append(('date_order', '<=', dt_to))
        if config_ids:
            domain.append(('config_id', 'in', config_ids))

        orders = self.env['pos.order'].search(domain)

        summary = defaultdict(lambda: {'qty': 0.0, 'total': 0.0, 'price_sum': 0.0, 'count': 0})
        not_invoiced = []
        discount_count = 0
        discount_total = 0.0
        for order in orders:
            if not order.account_move:
                not_invoiced.append(order.name)
            for line in order.lines:
                if line.discount:
                    discount_count += 1
                    discount_total += (line.price_unit * line.qty * line.discount) / 100.0
                prod = line.product_id.display_name
                summary[prod]['qty'] += line.qty
                summary[prod]['total'] += line.price_subtotal_incl
                summary[prod]['price_sum'] += line.price_unit
                summary[prod]['count'] += 1

        products = []
        for name, vals in summary.items():
            avg_price = vals['price_sum']/vals['count'] if vals['count'] else 0.0
            products.append({
                'name': name,
                'price': avg_price,
                'qty': vals['qty'],
                'total': vals['total'],
            })

        return {
            'date_from': date_from,
            'date_to': date_to,
            'config_names': ', '.join(self.env['pos.config'].browse(config_ids).mapped('name')) if config_ids else 'All',
            'products': sorted(products, key=lambda p: p['name']),
            'total_amount': sum(p['total'] for p in products),
            'total_transactions': len(orders),
            'discount_count': discount_count,
            'discount_total': discount_total,
            'not_invoiced': not_invoiced,
        }
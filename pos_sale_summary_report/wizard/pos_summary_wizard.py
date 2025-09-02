from odoo import models, fields
from datetime import datetime, time

class PosSummaryWizard(models.TransientModel):
    _name = "pos.summary.wizard"
    _description = "POS Sales Summary Wizard"

    config_ids = fields.Many2many("pos.config", string="POS Configurations")
    date_from = fields.Date(string="From", required=True, default=fields.Date.context_today)
    date_to = fields.Date(string="To", required=True, default=fields.Date.context_today)

    def action_print(self):
        self.ensure_one()
        dt_from = datetime.combine(self.date_from, time.min)
        dt_to = datetime.combine(self.date_to, time.max)

        # Example: compute summary_by_date
        summary_by_date = {}
        orders = self.env['pos.order'].search([
            ('date_order', '>=', dt_from),
            ('date_order', '<=', dt_to),
            ('config_id', 'in', self.config_ids.ids)
        ])
        for order in orders:
            date_str = order.date_order.strftime('%Y-%m-%d')
            if date_str not in summary_by_date:
                summary_by_date[date_str] = []
            for line in order.lines:
                summary_by_date[date_str].append({
                    'product_name': line.product_id.name,
                    'qty': line.qty,
                    'total': line.price_subtotal,
                })

        data = {
            'date_from': dt_from.strftime("%Y-%m-%d"),
            'date_to': dt_to.strftime("%Y-%m-%d"),
            'summary_by_date': summary_by_date,
        }

        report_ref = self.env.ref('pos_sale_summary_report.action_pos_summary_report')
        return report_ref.report_action(self, data=data)

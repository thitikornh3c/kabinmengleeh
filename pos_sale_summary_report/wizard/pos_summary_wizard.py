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

        # Convert wizard dates to UTC datetime strings for proper search
        dt_from = fields.Datetime.to_string(datetime.combine(self.date_from, time.min))
        dt_to = fields.Datetime.to_string(datetime.combine(self.date_to, time.max))

        # Compute summary by date
        summary_by_date = {}
        orders = self.env['pos.order'].search([
            ('date_order', '>=', dt_from),
            ('date_order', '<=', dt_to),
            ('config_id', 'in', self.config_ids.ids)
        ])

        for order in orders:
            # Convert order.date_order to local date string for grouping
            local_date = fields.Date.to_string(order.date_order)  # 'YYYY-MM-DD'
            if local_date not in summary_by_date:
                summary_by_date[local_date] = []
            for line in order.lines:
                summary_by_date[local_date].append({
                    'product_name': line.product_id.name,
                    'qty': line.qty,
                    'total': line.price_subtotal,
                })

        report_data = {
            'date_from': fields.Date.to_string(self.date_from),
            'date_to': fields.Date.to_string(self.date_to),
            'summary_by_date': summary_by_date,
            'ids': self.ids,  # optional for reference
        }

        report_ref = self.env.ref('pos_sale_summary_report.action_pos_summary_report')
        return report_ref.report_action(self, data={'data': report_data})

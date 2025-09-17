from odoo import models, fields
from datetime import datetime, time, timedelta

class PosSummaryWizard(models.TransientModel):
    _name = "pos.summary.wizard"
    _description = "POS Sales Summary Wizard"

    config_ids = fields.Many2many("pos.config", string="POS Configurations")
    date_from = fields.Date(string="From", required=True, default=fields.Date.context_today)
    date_to = fields.Date(string="To", required=True, default=fields.Date.context_today)

    def action_print(self):
        self.ensure_one()

        # Convert wizard dates (local) to UTC datetime for DB search
        local_dt_from = datetime.combine(self.date_from, time.min)
        local_dt_to = datetime.combine(self.date_to, time.max)

        # Adjust your timezone offset (Bangkok = UTC+7)
        utc_dt_from = local_dt_from - timedelta(hours=7)
        utc_dt_to = local_dt_to - timedelta(hours=7)

        # Search POS orders within UTC range
        orders = self.env['pos.order'].search([
            ('date_order', '>=', utc_dt_from),
            ('date_order', '<=', utc_dt_to),
            ('config_id', 'in', self.config_ids.ids)
        ])

        # Group order lines by date (local)
        summary_by_date = {}
        for order in orders:
            local_date = fields.Date.to_string(order.date_order + timedelta(hours=7))  # convert UTC to local date
            if local_date not in summary_by_date:
                summary_by_date[local_date] = []
            for line in order.lines:
                summary_by_date[local_date].append({
                    'product_name': line.product_id.name,
                    'qty': line.qty,
                    'total': line.price_subtotal,
                })


        pending_invoicing_orders = self.env['pos.order'].search([
            ('partner_id', '!=', False),
            ('account_move', '=', False),
        ]).filtered(lambda o: any(line.tax_ids for line in o.lines))
        pending_orders_data = [{
            'name': order.name,
            'date_order': fields.Datetime.to_string(order.date_order.astimezone(user_tz)),
            'customer': order.partner_id.name if order.partner_id else '',
            'vat': order.partner_id.vat or '',
            'amount_total': order.amount_total,
            'amount_tax': order.amount_tax,
        } for order in pending_invoicing_orders]
        # Prepare data for QWeb template
        report_data = {
            'date_from': fields.Date.to_string(self.date_from),
            'date_to': fields.Date.to_string(self.date_to),
            'summary_by_date': summary_by_date,
            'ids': self.ids,
            'orders': [{
                'name': order.name,
                'date_order': fields.Datetime.to_string(order.date_order + timedelta(hours=7)),
                'lines': [{
                    'product_name': line.product_id.name,
                    'qty': line.qty,
                    'total': line.price_subtotal,
                } for line in order.lines],
            } for order in orders],
            'waiting_invoice': pending_orders_data
        }
        

        # Call the report
        report_ref = self.env.ref('pos_sale_summary_report.action_pos_summary_report')
        return report_ref.report_action(self, data={'data': report_data})

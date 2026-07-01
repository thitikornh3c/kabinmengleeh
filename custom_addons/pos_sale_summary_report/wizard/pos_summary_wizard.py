from odoo import api, models, fields, _
from odoo.exceptions import UserError
from datetime import datetime, time, timedelta


class PosSummaryWizard(models.TransientModel):
    _name = "pos.summary.wizard"
    _description = "POS Sales Summary Wizard"

    config_ids = fields.Many2many("pos.config", string="POS Configurations")
    date_from = fields.Date(string="From", required=True, default=fields.Date.context_today)
    date_to = fields.Date(string="To", required=True, default=fields.Date.context_today)

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if 'config_ids' in fields_list and not res.get('config_ids'):
            configs = self.env['pos.config'].search([
                ('company_id', 'in', self.env.companies.ids),
            ])
            if configs:
                res['config_ids'] = [(6, 0, configs.ids)]
        return res

    def _get_config_ids(self):
        self.ensure_one()
        if self.config_ids:
            return self.config_ids.ids
        return self.env['pos.config'].search([
            ('company_id', 'in', self.env.companies.ids),
        ]).ids

    def _local_to_utc_range(self):
        self.ensure_one()
        local_dt_from = datetime.combine(self.date_from, time.min)
        local_dt_to = datetime.combine(self.date_to, time.max)
        # Bangkok UTC+7
        return local_dt_from - timedelta(hours=7), local_dt_to - timedelta(hours=7)

    def _prepare_report_data(self):
        self.ensure_one()
        utc_dt_from, utc_dt_to = self._local_to_utc_range()
        config_ids = self._get_config_ids()

        orders = self.env['pos.order'].search([
            ('date_order', '>=', utc_dt_from),
            ('date_order', '<=', utc_dt_to),
            ('config_id', 'in', config_ids),
            ('state', '!=', 'cancel'),
        ])

        summary_by_date = {}
        for order in orders:
            local_date = fields.Date.to_string(order.date_order + timedelta(hours=7))
            summary_by_date.setdefault(local_date, [])
            for line in order.lines:
                summary_by_date[local_date].append({
                    'product_name': line.product_id.display_name,
                    'qty': line.qty,
                    'total': line.price_subtotal,
                })

        pending_invoicing_orders = self.env['pos.order'].search([
            ('partner_id', '!=', False),
            ('account_move', '=', False),
            ('config_id', 'in', config_ids),
            ('date_order', '>=', utc_dt_from),
            ('date_order', '<=', utc_dt_to),
            ('state', '!=', 'cancel'),
        ]).filtered(lambda o: any(line.tax_ids for line in o.lines))

        pending_orders_data = []
        for order in pending_invoicing_orders:
            partner = order.partner_id.with_company(order.company_id).sudo()
            pending_orders_data.append({
                'name': order.name,
                'date_order': fields.Datetime.to_string(order.date_order + timedelta(hours=7)),
                'customer': partner.name or '',
                'vat': partner.vat or '',
                'amount_total': order.amount_total,
                'amount_tax': order.amount_tax,
            })

        return {
            'date_from': fields.Date.to_string(self.date_from),
            'date_to': fields.Date.to_string(self.date_to),
            'config_names': ', '.join(self.env['pos.config'].browse(config_ids).mapped('name')),
            'order_count': len(orders),
            'summary_by_date': summary_by_date,
            'orders': [{
                'name': order.name,
                'date_order': fields.Datetime.to_string(order.date_order + timedelta(hours=7)),
                'lines': [{
                    'product_name': line.product_id.display_name,
                    'qty': line.qty,
                    'total': line.price_subtotal,
                } for line in order.lines],
            } for order in orders],
            'pending_orders': pending_orders_data,
        }

    def action_print(self):
        self.ensure_one()
        if not self._get_config_ids():
            raise UserError(_('Please select at least one POS configuration.'))

        report_data = self._prepare_report_data()
        report_ref = self.env.ref('pos_sale_summary_report.action_pos_summary_report')
        return report_ref.report_action(self.ids, data={'report_data': report_data})

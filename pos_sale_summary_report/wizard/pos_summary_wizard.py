# Wizard
class PosSummaryWizard(models.TransientModel):
    _name = "pos.summary.wizard"

    config_ids = fields.Many2many("pos.config")
    date_from = fields.Date(default=fields.Date.context_today)
    date_to = fields.Date(default=fields.Date.context_today)
    summary_by_date = fields.Serialized('Summary by date')

    def action_print(self):
        self.ensure_one()
        dt_from = datetime.combine(self.date_from, time.min)
        dt_to = datetime.combine(self.date_to, time.max)

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
        # store summary in wizard field
        self.summary_by_date = summary_by_date

        report_ref = self.env.ref('pos_sale_summary_report.action_pos_summary_report')
        return report_ref.report_action(self)

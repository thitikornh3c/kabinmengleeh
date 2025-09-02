from odoo import models, fields

class POSSummaryWizard(models.TransientModel):
    _name = "pos.summary.wizard"
    _description = "POS Summary Wizard"

    date_from = fields.Date(string="Start Date", required=True)
    date_to = fields.Date(string="End Date", required=True)

    def action_print_report(self):
        domain = [('date_order', '>=', self.date_from),
                  ('date_order', '<=', self.date_to)]
        orders = self.env['pos.order'].search(domain)
        return self.env.ref('pos_daily_summary.action_report_pos_summary').report_action(orders)

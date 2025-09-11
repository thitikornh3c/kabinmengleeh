from odoo import api, models
from collections import defaultdict

class ReportPOSSummary(models.AbstractModel):
    _name = "report.pos_daily_summary_report.report_pos_summary_template"
    _description = "POS Daily Summary Report"

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['pos.order'].browse(docids)
        grouped_sales = defaultdict(lambda: {"products": [], "total": 0.0, "qty": 0})
        currency = self.env.company.currency_id

        # Group sales by day
        for order in docs:
            date_key = order.date_order.strftime("%d-%m-%Y")
            for line in order.lines:
                grouped_sales[date_key]["products"].append({
                    "product_name": line.product_id.display_name,
                    "price": line.price_unit,
                    "quantity": line.qty,
                    "total": line.price_subtotal_incl,
                })
                grouped_sales[date_key]["total"] += line.price_subtotal_incl
                grouped_sales[date_key]["qty"] += line.qty

        # Sale Orders
        invoiced_orders = self.env['sale.order'].search([('invoice_status', '=', 'invoiced')])
        not_invoiced_orders = self.env['sale.order'].search([('invoice_status', '!=', 'invoiced')])

        return {
            "doc_ids": docids,
            "doc_model": "pos.order",
            "docs": docs,
            "grouped_sales": grouped_sales,
            "currency": currency,
            "invoiced_orders": invoiced_orders,
            "not_invoiced_orders": not_invoiced_orders,
        }

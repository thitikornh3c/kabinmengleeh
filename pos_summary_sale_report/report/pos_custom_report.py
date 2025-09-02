from odoo import models

class POSCustomSaleReport(models.AbstractModel):
    _name = "report.pos_custom_sale_report.report_pos_custom"
    _description = "Custom POS Sale Report"

    def _get_report_values(self, docids, data=None):
        docs = self.env["pos.order"].browse(docids)

        # Example: group by product
        summary = {}
        for order in docs:
            for line in order.lines:
                product = line.product_id.display_name
                if product not in summary:
                    summary[product] = {
                        "qty": 0,
                        "total": 0.0,
                        "price": line.price_unit,
                    }
                summary[product]["qty"] += line.qty
                summary[product]["total"] += line.price_subtotal_incl

        return {
            "doc_ids": docids,
            "doc_model": "pos.order",
            "docs": docs,
            "summary": summary,
        }

from odoo import fields, models

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    pc_show_tax_on_report = fields.Boolean(
        string="Show Tax on Report", 
        store=True,
        help="To show the tax on the quotation/order PDF print")
    
    pc_remittance_info = fields.Html(
        string="Remittance Info",
        store=True,
    )
    
    pc_show_remittance_info = fields.Boolean(
        string="Show Remittance Info in printed PDF?",
        store=True,
    )

    pc_show_sign_stamp = fields.Boolean(
        string="Show Sign and Stamp on PDF",
    )

    def _get_order_lines_to_report(self):
        lines = super()._get_order_lines_to_report()
        return lines.filtered(lambda l: not l.pc_suppress_in_report)

from odoo import fields, models, api
from odoo.exceptions import ValidationError

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    pc_suppress_in_report = fields.Boolean(string="Suppress")

    @api.constrains('pc_suppress_in_report', 'price_unit')
    def _check_suppress_price_unit(self):
        for line in self:
            if line.pc_suppress_in_report and line.price_unit != 0:
                raise ValidationError(
                    "Order lines marked as 'Suppress in Report' must have Unit Price = 0."
                )
    
    def _prepare_invoice_line(self, **optional_values):
        res = super()._prepare_invoice_line(**optional_values)
        res.update({
            'pc_suppress_in_report': self.pc_suppress_in_report,
        })
        return res

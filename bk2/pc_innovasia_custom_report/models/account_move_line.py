from odoo import fields, models, api
from odoo.exceptions import ValidationError

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    pc_suppress_in_report = fields.Boolean(string="Suppress")

    @api.constrains('pc_suppress_in_report', 'price_unit')
    def _check_suppress_price_unit(self):
        for line in self:
            if line.pc_suppress_in_report and line.price_unit != 0.0:
                raise ValidationError(
                    "Invoice lines marked as 'Suppress in Report' must have Unit Price = 0."
                )

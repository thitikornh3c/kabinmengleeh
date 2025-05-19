from odoo import models, api
import math
import logging
_logger = logging.getLogger(__name__)

class AccountTax(models.Model):
    _inherit = 'account.tax'

    @api.model
    def _round_tax_amount(self, amount, currency=None):
        # Check for invoice name condition in context
        invoice = self.env.context.get('invoice')
        _logger.info(f"ReComputed invoice: {invoice}")
        if invoice and invoice.name == 'INV20250228001':
            # Custom rounding: round down
            precision = currency.decimal_places if currency else 2
            factor = 10 ** precision
            return math.floor(amount * factor) / factor
        else:
            # Default Odoo rounding
            return currency.round(amount) if currency else round(amount, 2)

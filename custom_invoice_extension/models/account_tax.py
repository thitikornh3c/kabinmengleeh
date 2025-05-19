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

    @api.model
    def _compute_amount(self, base_amount, price_unit, quantity=1.0, product=None, partner=None, is_refund=False):
            """Override the tax computation to round down for a specific invoice"""
            tax_amount = super()._compute_amount(
                base_amount, price_unit, quantity, product, partner, is_refund
            )
            invoice = self.env.context.get('invoice')
            currency = self.env.context.get('currency')  # Optional, if passed
            _logger.info(f"Custom Rounding: Invoice in context: {invoice}")

            if invoice and invoice.name == 'INV20250228001':
                precision = currency.decimal_places if currency else 2
                factor = 10 ** precision
                tax_amount = math.floor(tax_amount * factor) / factor
                _logger.info(f"Rounding down tax for {invoice.name}: {tax_amount}")
            
            return tax_amount
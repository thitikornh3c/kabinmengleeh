from odoo import models, api
import logging
_logger = logging.getLogger(__name__)

class CustomInvoice(models.Model):
    _inherit = 'account.move'

    @api.model
    def create(self, vals):
        _logger.info(f"Invoice Code: {vals['name']}")
        if vals.get('move_type') in ('out_invoice', 'in_invoice'):
            # Use your custom sequence logic
            vals['name'] = self.env['ir.sequence'].next_by_code('account.move')

        return super(CustomInvoice, self).create(vals)
from odoo import models, api
import logging
_logger = logging.getLogger(__name__)

class CustomInvoice(models.Model):
    _inherit = 'account.move'

    @api.model
    def create(self, vals):
        _logger.info(f"Invoice Code: {vals}")
        move_type = vals.get('move_type', '')
        
        if move_type == 'out_invoice':
            # Use your custom sequence logic
            if vals.get('state') == 'draft':
                vals['name'] = 'Draft'  # Set the name to "Draft" for draft invoices
            else:
                vals['name'] = self.env['ir.sequence'].next_by_code('account.move')
        elif move_type == 'in_invoice':
            # Use your custom sequence logic
            if vals.get('state') == 'draft':
                vals['name'] = 'Draft'  # Set the name to "Draft" for draft invoices
            else:
                vals['name'] = self.env['ir.sequence'].next_by_code('account.bill.move')

        return super(CustomInvoice, self).create(vals)
from odoo import models, api
from datetime import datetime

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.model
    def create(self, vals):
        # Assuming the sequence is stored in the 'name' field
        sequence_code = 'sale.order'  # Replace with your actual sequence code
        sequence = self.env['ir.sequence'].search([('code', '=', sequence_code)], limit=1)

        if sequence:
            current_date = datetime.now().strftime("%Y-%m-%d")
            if sequence.x_studio_last_date != current_date:
                sequence.number_next = 1  # Reset the sequence number
                sequence.x_studio_last_date = current_date  # Update last date

        # Call the super method to create the sale order
        return super(SaleOrder, self).create(vals)
from odoo import _, api, fields, models
from odoo.exceptions import UserError
from datetime import datetime
import logging
_logger = logging.getLogger(__name__)

class CustomSequence(models.Model):
    _inherit = 'ir.sequence'

    # last_reset_date = fields.Datetime(string='Last Reset Date', readonly=True)
                                  
    def _get_buddha_era_year(self):
        # Calculate Buddha Era year
        current_year = datetime.now().year
        be_year = current_year + 543
        month_date = datetime.now().strftime("%m%d")
        return f"{str(be_year)[2:4]}{month_date}"

    def _get_prefix_suffix(self):
        """
        Override to customize the sequence prefix and suffix.
        """
        # Call the super method to get the default prefix and suffix
        currentDate = datetime.now().strftime("%d")
        _logger.info(f"Sequnece Entry: {self.code} {self.number_next} | {currentDate} {self.x_studio_last_date}")
    
        if currentDate != self.x_studio_last_date:
            sequence = self.search([('code', '=', self.code)], limit=1)
            sequence.number_next = 1

        prefix, suffix = super()._get_prefix_suffix()
        # next_by_code = super().next_by_code(self.code)
        # _logger.info(f"Sequnece Entry: {next_by_code}")
        be_year = self._get_buddha_era_year()

        # Optionally modify the prefix
        if self.prefix:
            prefix = f"{self.prefix}{be_year}"

        self.x_studio_last_date = currentDate
        # self.number_next = 1
        # prefix = f"{self.code}{be_year}"
        # Customize the suffix
        # For example, include the Buddha Era year in the suffix
      
        # suffix = f"{be_year}/{suffix}" if suffix else f"{be_year}"

        return prefix, suffix
    


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
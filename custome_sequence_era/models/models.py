from odoo import _, api, fields, models
from odoo.exceptions import UserError
from datetime import datetime, timedelta
import logging
_logger = logging.getLogger(__name__)

class CustomSequence(models.Model):
    _inherit = 'ir.sequence'

    # last_reset_date = fields.Datetime(string='Last Reset Date', readonly=True)
                                  
    def _get_buddha_era_year(self):
        # Calculate Buddha Era year
        current_year = datetime.now().year
        be_year = current_year + 543
        month_date = datetime.now().strftime("%m")
        return f"{str(be_year)[2:4]}{month_date}"

    def _get_prefix_suffix(self):
        """
        Override to customize the sequence prefix and suffix.
        """
        # Call the super method to get the default prefix and suffix
        # Get the current UTC time
        utc_now = datetime.utcnow()

        # Bangkok is UTC+7
        bangkok_time = utc_now + timedelta(hours=7)

        currentDate = bangkok_time.strftime("%d")
        _logger.info(f"Sequnece Entry: {self.code} {self.number_next} | {bangkok_time} {currentDate} {self.x_studio_last_date}")
    
        if currentDate != self.x_studio_last_date:
            sequence = self.search([('code', '=', self.code)], limit=1)
            sequence.number_next = 1

        prefix, suffix = super()._get_prefix_suffix()
        # next_by_code = super().next_by_code(self.code)
        # _logger.info(f"Sequnece Entry: {next_by_code}")
        be_year = self._get_buddha_era_year()

        # Optionally modify the prefix
        if self.prefix:
            prefix = f"{self.prefix}{be_year}{currentDate}"

        self.x_studio_last_date = currentDate
        # self.number_next = 1
        # prefix = f"{self.code}{be_year}"
        # Customize the suffix
        # For example, include the Buddha Era year in the suffix
      
        # suffix = f"{be_year}/{suffix}" if suffix else f"{be_year}"

        return prefix, suffix
    
    @api.model
    def next_by_code(self, code, **kwargs):
        """Override next_by_code to reset number_next if needed."""
        sequence = self.search([('code', '=', code)], limit=1)
        _logger.warning(f"Sequence code '{code}' {kwargs} not found.")
        
        if sequence:
            # Call _get_prefix_suffix to update number_next if needed
            sequence._get_prefix_suffix()

            # Call the original next_by_code to get the next number
            next_number = super(CustomSequence, sequence).next_by_code(code, **kwargs)

            # Combine the prefix and next number to form the full sequence value
            # prefix, _ = sequence._get_prefix_suffix()  # Get the updated prefix
            return f"{next_number}"  # Adjust as needed

        # Handle case where sequence is not found
        return super(CustomSequence, self).next_by_code(code, **kwargs)
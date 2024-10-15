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
        prefix, suffix = super()._get_prefix_suffix()
        be_year = self._get_buddha_era_year()
        _logger.info(f"Sequnece Entry: {self.code} {self.number_next} {self.x_studio_last_date}")
        currentDate = datetime.now().strftime("%d")
        if currentDate != self.x_studio_last_date:
            self.number_next = 1
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

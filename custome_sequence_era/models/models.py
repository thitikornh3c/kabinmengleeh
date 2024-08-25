from odoo import _, api, fields, models
from odoo.exceptions import UserError
from datetime import datetime

class CustomSequence(models.Model):
    _inherit = 'ir.sequence'

    def _get_buddha_era_year(self):
        # Calculate Buddha Era year
        current_year = datetime.now().year
        be_year = current_year + 543
        return be_year

    def _next_number(self):
        # Custom sequence generation logic
        be_year = self._get_buddha_era_year()
        # Call the parent method to get the next number
        next_number = super()._next_number()
        # Modify the sequence format to include BE year
        # Format: BE_YEAR/SEQUENCE_NUMBER
        return f"{be_year}/{next_number}"

    def _get_next_number(self):
        # Override default format to include custom year
        sequence_number = super()._get_next_number()
        be_year = self._get_buddha_era_year()
        return f"{be_year}/{sequence_number}"
    
    def _get_prefix_suffix(self, date=None, date_range=None):
        interpolated_prefix = (self.prefix) if self.prefix else ""
        interpolated_suffix = (self.suffix) if self.suffix else ""
        return  interpolated_prefix, interpolated_suffix

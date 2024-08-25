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

    def _get_prefix_suffix(self):
        """
        Override to customize the sequence prefix and suffix.
        """
        # Call the super method to get the default prefix and suffix
        prefix, suffix = super()._get_prefix_suffix()

        # Optionally modify the prefix
        if self.prefix:
            prefix = f"{self.prefix}{be_year}"

        # Customize the suffix
        # For example, include the Buddha Era year in the suffix
        be_year = self._get_buddha_era_year()
        # suffix = f"{be_year}/{suffix}" if suffix else f"{be_year}"

        return prefix, suffix

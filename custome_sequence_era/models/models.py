from odoo import models, fields
from datetime import datetime

class CustomSequence(models.Model):
    _inherit = 'ir.sequence'

    def _get_buddha_era_year(self):
        current_year = datetime.now().year
        be_year = current_year + 543
        return be_year

    def _next_number(self):
        # Override the default _next_number method
        next_number = super()._next_number()
        be_year = self._get_buddha_era_year()
        # Modify the sequence format to include BE year
        return f"{be_year}/{next_number}"
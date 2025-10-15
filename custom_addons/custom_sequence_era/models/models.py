from odoo import models, api, fields
from datetime import datetime, timedelta
import logging
_logger = logging.getLogger(__name__)

class CustomSequence(models.Model):
    _inherit = 'ir.sequence'

    x_studio_last_date = fields.Char(string="Last Date", readonly=False)
    x_studio_last_year = fields.Char(string="Last Year", readonly=False)

    def _get_buddha_year(self):
        """Return Buddhist year (2568 = 2025 + 543)."""
        now = datetime.utcnow() + timedelta(hours=7)
        return now.year + 543, now

    @api.model
    def next_by_code(self, code, **kwargs):
        """Custom next number logic for INV and SQ patterns."""
        company_id = self.env.context.get('company_id', self.env.company.id)
        sequence_code = f"{code}.h3c" if company_id == 2 else code

        sequence = self.search([('code', '=', sequence_code)], limit=1)
        if not sequence:
            return super(CustomSequence, self).next_by_code(code, **kwargs)

        prefix = sequence.prefix or ''
        be_year, now = self._get_buddha_year()
        current_date = now.strftime("%Y%m%d")
        short_be_year = str(be_year)[2:]  # last two digits of BE year
        current_day = now.strftime("%d")
        current_year = now.strftime("%Y")

        _logger.info(f"SEQ DEBUG: code={sequence_code}, prefix={prefix}, last_date={sequence.x_studio_last_date}, last_year={sequence.x_studio_last_year}")

        # ---------- INVOICE PATTERN ----------
        if prefix.startswith("INV"):
            # Reset every day
            if sequence.x_studio_last_date != current_date:
                sequence.number_next = 1
                sequence.x_studio_last_date = current_date
                _logger.info(f"RESET daily sequence for {sequence_code}")

            next_number = sequence.number_next
            sequence.number_next += 1

            full_number = f"{prefix}{current_date}{str(next_number).zfill(3)}"
            return full_number

        # ---------- SALE ORDER PATTERN ----------
        elif prefix.startswith("SQ"):
            # Reset every new Buddhist year
            if sequence.x_studio_last_year != str(be_year):
                sequence.number_next = 1
                sequence.x_studio_last_year = str(be_year)
                _logger.info(f"RESET yearly sequence for {sequence_code}")

            next_number = sequence.number_next
            sequence.number_next += 1

            # Format: SQ + BE(year last 2 digits) + MMDD + running 5 digits
            full_number = f"{prefix}{short_be_year}{now.strftime('%m%d')}{str(next_number).zfill(5)}"
            return full_number

        # ---------- OTHER SEQUENCES ----------
        else:
            return super(CustomSequence, sequence).next_by_code(sequence_code, **kwargs)

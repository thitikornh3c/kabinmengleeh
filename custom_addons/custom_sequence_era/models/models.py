from odoo import _, api, fields, models
from odoo.exceptions import UserError
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)

class CustomSequence(models.Model):
    _inherit = 'ir.sequence'

    # ---------------------------------------------------------------
    # Helper functions
    # ---------------------------------------------------------------
    def _get_buddha_era_year(self):
        """Return Buddhist Era year + month (e.g. '6805' for May 2568 BE)."""
        current_year = datetime.now().year
        be_year = current_year + 543
        month_date = datetime.now().strftime("%m")
        return f"{str(be_year)[2:4]}{month_date}"

    def _get_bangkok_time(self):
        """Return datetime in Bangkok timezone (UTC+7)."""
        utc_now = datetime.utcnow()
        return utc_now + timedelta(hours=7)

    # ---------------------------------------------------------------
    # Custom Prefix Generators
    # ---------------------------------------------------------------
    def _get_prefix_suffix_buddha_era(self):
        """Custom prefix for sale orders or Buddhist Era documents."""
        bangkok_time = self._get_bangkok_time()
        current_day = bangkok_time.strftime("%d")

        company_id = self.env.context.get('company_id', self.env.company.id)
        sequence_code = self.code
        if company_id == 2:
            sequence_code += '.h3c'

        sequence = self.search([('code', '=', sequence_code)], limit=1)
        if sequence and current_day != sequence.x_studio_last_date:
            sequence.number_next = 1
            sequence.x_studio_last_date = current_day

        prefix, suffix = ('', '')
        if sequence:
            prefix, suffix = super(CustomSequence, sequence)._get_prefix_suffix()

            be_year = self._get_buddha_era_year()
            if sequence.prefix:
                prefix = f"{sequence.prefix}{be_year}{current_day}"

        _logger.info(f"[SEQ-BE] {sequence_code}: prefix={prefix}, next={sequence.number_next if sequence else 'N/A'}")
        return prefix, suffix

    def _get_prefix_suffix_inv(self):
        """Custom prefix for invoice pattern INV%y%m%d%03d (reset daily)."""
        bangkok_time = self._get_bangkok_time()
        current_day = bangkok_time.strftime("%d")
        year = bangkok_time.strftime("%y")
        month = bangkok_time.strftime("%m")

        company_id = self.env.context.get('company_id', self.env.company.id)
        sequence_code = self.code
        if company_id == 2:
            sequence_code += '.h3c'

        sequence = self.search([('code', '=', sequence_code)], limit=1)
        if sequence and current_day != sequence.x_studio_last_date:
            sequence.number_next = 1
            sequence.x_studio_last_date = current_day

        prefix, suffix = ('', '')
        if sequence:
            prefix, suffix = super(CustomSequence, sequence)._get_prefix_suffix()

            if sequence.prefix:
                prefix = f"{sequence.prefix}{year}{month}{current_day}"

        _logger.info(f"[SEQ-INV] {sequence_code}: prefix={prefix}, next={sequence.number_next if sequence else 'N/A'}")
        return prefix, suffix

    # ---------------------------------------------------------------
    # Override next_by_code
    # ---------------------------------------------------------------
    @api.model
    def next_by_code(self, code, **kwargs):
        """Override next_by_code to apply different sequence patterns."""
        company_id = self.env.context.get('company_id', self.env.company.id)
        sequence_code = code
        if company_id == 2:
            sequence_code += '.h3c'

        sequence = self.search([('code', '=', sequence_code)], limit=1)
        _logger.info(f"[SEQ] next_by_code called for {sequence_code}")

        if not sequence:
            _logger.warning(f"[SEQ] Sequence code '{sequence_code}' not found, fallback to super()")
            return super(CustomSequence, self).next_by_code(sequence_code, **kwargs)

        # Choose the prefix rule
        if 'account.move' in sequence.code:
            sequence._get_prefix_suffix_inv()
        elif 'sale.order' in sequence.code:
            sequence._get_prefix_suffix_buddha_era()

        # Generate next number
        next_number = super(CustomSequence, sequence).next_by_code(sequence_code, **kwargs)
        _logger.info(f"[SEQ] Generated {next_number} for {sequence_code}")
        return next_number

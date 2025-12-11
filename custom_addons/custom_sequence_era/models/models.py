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

    def _get_next_invoice_number(self, sequence):
        """Return the next INV number, filling gaps if any."""
        now = datetime.utcnow() + timedelta(hours=7)
        current_date = now.strftime("%Y%m%d")

        # Reset daily if needed
        if self.x_studio_last_date != current_date:
            self.number_next = 1
            self.x_studio_last_date = current_date

        prefix = sequence.prefix or ''
        padding = 3  # INV running digits

        # Get all existing numbers for today
        model = self.env['account.move']  # adjust for invoice model
        domain = [
            ('name', 'like', f"{prefix}{current_date}%")
        ]
        existing_numbers = model.search(domain).mapped('name')

        # Find first missing number
        for i in range(1, 999):
            candidate = f"{prefix}{current_date}{str(i).zfill(padding)}"
            if candidate not in existing_numbers:
                sequence.number_next = i + 1
                return candidate

        # fallback if somehow full
        sequence.number_next += 1
        return f"{prefix}{current_date}{str(sequence.number_next - 1).zfill(padding)}"
    
    def _get_prefix_suffix(self):
        """
        Override to customize the sequence prefix and suffix.
        """

        if self.code in (None, "", False):
            prefix, suffix = super()._get_prefix_suffix()
            return prefix, suffix

        # Get Bangkok timezone timestamp
        utc_now = datetime.utcnow()
        bangkok_time = utc_now + timedelta(hours=7)
        currentDate = bangkok_time.strftime("%d")

        company_id = self.env.context.get('company_id', self.env.company.id)
        _logger.info(f"Sequence of Company: {company_id}")

        sequence_code = self.code
        if company_id == 2:
            sequence_code = sequence_code + '.h3c'

        _logger.info(
            f"Sequence Entry: {sequence_code} {self.number_next} | "
            f"{bangkok_time} {currentDate} {self.x_studio_last_date}"
        )

        # --- get default prefix/suffix ---
        prefix, suffix = super()._get_prefix_suffix()

        # Normalize prefix/suffix (important!)
        prefix = prefix or ""
        suffix = suffix or ""
        self_prefix = self.prefix or ""

        # --- Custom logic for INV / REC ---
        if str(prefix).startswith("INV"):
            sequence = self.search([('code', '=', self.code)], limit=1)
            if currentDate != self.x_studio_last_date:
                sequence.number_next = 1
            else:
                self._get_next_invoice_number(sequence)

        if str(prefix).startswith("REC"):
            sequence = self.search([('code', '=', self.code)], limit=1)
            if currentDate != self.x_studio_last_date:
                sequence.number_next = 1
            else:
                self._get_next_invoice_number(sequence)

        # Buddha Era Year
        be_year = self._get_buddha_era_year()

        # ---- Build custom PREFIX safely ----
        if str(self_prefix).startswith("SQ"):
            prefix = f"{self_prefix}{be_year}{currentDate}"

        elif str(self_prefix).startswith("INV"):
            prefix = f"{self_prefix}{bangkok_time.strftime('%Y%m')}{currentDate}"

        elif str(self_prefix).startswith("REC"):
            prefix = f"{self_prefix}{bangkok_time.strftime('%Y%m')}{currentDate}"

        else:
            prefix = f"{self_prefix}{be_year}{currentDate}"

        # Update last date
        self.x_studio_last_date = currentDate

        _logger.info(
            f"Sequence Entry: {sequence_code} {self.number_next} | "
            f"{bangkok_time} {currentDate} {self.x_studio_last_date} "
            f"{prefix} {suffix}"
        )

        return prefix, suffix

    
    @api.model
    def next_by_code(self, code, **kwargs):
        """Override next_by_code to reset number_next if needed."""

        company_id = self.env.context.get('company_id', self.env.company.id)
        _logger.info(f"Sequnece of Company: {company_id} {code}")
        sequence_code = code
        if company_id == 2:
            sequence_code = sequence_code + '.h3c'

        sequence = self.search([('code', '=', sequence_code)], limit=1)
        _logger.warning(f"Sequence code '{sequence_code}' {sequence} not found.")
        
        if sequence:
            # Call _get_prefix_suffix to update number_next if needed
            sequence._get_prefix_suffix()

            # Call the original next_by_code to get the next number
            next_number = super(CustomSequence, sequence).next_by_code(sequence_code, **kwargs)
            _logger.warning(f"Sequence next_number '{next_number}'")

            # Combine the prefix and next number to form the full sequence value
            # prefix, _ = sequence._get_prefix_suffix()  # Get the updated prefix
            return f"{next_number}"  # Adjust as needed

        # Handle case where sequence is not found
        return super(CustomSequence, self).next_by_code(sequence_code, **kwargs)
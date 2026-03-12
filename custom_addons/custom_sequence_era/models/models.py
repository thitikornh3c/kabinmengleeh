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
        
        # Check company_id to determine padding
        company_id = self.env.context.get('company_id', self.env.company.id)
        if company_id == 4:
            padding = 2  # 2 digits for company_id == 4 (01, 02, ..., 99)
        else:
            padding = 3  # 3 digits for other companies (001, 002, ..., 999)

        # Get all existing numbers for today
        model = self.env['account.move']  # adjust for invoice model
        domain = [
            ('name', 'like', f"{prefix}{current_date}%")
        ]
        existing_numbers = model.search(domain).mapped('name')

        # Find first missing number
        max_range = 99 if company_id == 4 else 999
        for i in range(1, max_range + 1):
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
        
        _logger.warning(f"=== PREFIX_SUFFIX DEBUG === Called for sequence code: '{self.code}', prefix: '{self.prefix}'")

        if self.code in (None, "", False):
            prefix, suffix = super()._get_prefix_suffix()
            return prefix, suffix

        # Get Bangkok timezone timestamp
        utc_now = datetime.utcnow()
        bangkok_time = utc_now + timedelta(hours=7)
        currentDate = bangkok_time.strftime("%d")

        company_id = self.env.context.get('company_id', self.env.company.id)
        _logger.warning(f"Sequence of Company: {company_id}")
        _logger.warning(f"Current company from env: {self.env.company.id}")
        _logger.warning(f"Company name: {self.env.company.name}")

        sequence_code = self.code
        if company_id == 2:
            sequence_code = sequence_code + '.h3c'
        elif company_id == 4:
            sequence_code = sequence_code + '.im'

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
        
        _logger.info(f"After super() - prefix: '{prefix}', self_prefix: '{self_prefix}', code: '{self.code}'")

        # --- Custom logic for INV / REC / QO / Payment Receipt ---
        if str(prefix).startswith("INV"):
            sequence = self.search([('code', '=', self.code)], limit=1)
            if company_id == 4:
                # For company_id == 4, reset daily based on full date (YYYYMMDD)
                current_full_date = bangkok_time.strftime('%Y%m%d')
                if current_full_date != self.x_studio_last_date:
                    sequence.number_next = 1
                    self.x_studio_last_date = current_full_date
            else:
                if currentDate != self.x_studio_last_date:
                    sequence.number_next = 1
                else:
                    self._get_next_invoice_number(sequence)

        # Handle REC, PBNK, or any receipt-related prefixes
        if (str(prefix).startswith("REC") or str(prefix).startswith("PBNK") or 
            str(self_prefix).startswith("REC") or str(self_prefix).startswith("PBNK") or
            'receipt' in str(self.code).lower() or 'payment' in str(self.code).lower() or
            str(self.code) == 'account.payment.im'):
            sequence = self.search([('code', '=', self.code)], limit=1)
            if company_id == 4:
                # For company_id == 4, reset daily based on full date (YYYYMMDD)
                current_full_date = bangkok_time.strftime('%Y%m%d')
                if current_full_date != self.x_studio_last_date:
                    sequence.number_next = 1
                    self.x_studio_last_date = current_full_date
            else:
                if currentDate != self.x_studio_last_date:
                    sequence.number_next = 1
                else:
                    self._get_next_invoice_number(sequence)

        if str(prefix).startswith("QO") or str(self_prefix).startswith("SO"):
            sequence = self.search([('code', '=', self.code)], limit=1)
            if company_id == 4:
                # For company_id == 4, reset daily based on full date (YYYYMMDD)
                current_full_date = bangkok_time.strftime('%Y%m%d')
                if current_full_date != self.x_studio_last_date:
                    sequence.number_next = 1
                    self.x_studio_last_date = current_full_date
            else:
                if currentDate != self.x_studio_last_date:
                    sequence.number_next = 1

        # Buddha Era Year
        be_year = self._get_buddha_era_year()

        # ---- Build custom PREFIX safely ----
        if str(self_prefix).startswith("SQ"):
            if company_id == 4:
                # For company_id == 4, use Buddha Era format: 25YYMMDD
                prefix = f"{self_prefix}{be_year}{currentDate}"
            else:
                prefix = f"{self_prefix}{be_year}{currentDate}"

        elif str(self_prefix).startswith("INV"):
            if company_id == 4:
                # For company_id == 4, use Buddha Era format: 25YYMMDD
                prefix = f"{self_prefix}{be_year}{currentDate}"
            else:
                prefix = f"{self_prefix}{bangkok_time.strftime('%Y%m')}{currentDate}"

        # Handle REC, PBNK, or any receipt-related prefixes
        elif (str(self_prefix).startswith("REC") or str(self_prefix).startswith("PBNK") or
              'receipt' in str(self.code).lower() or 'payment' in str(self.code).lower() or
              str(self.code) == 'account.payment.im'):
            if company_id == 4:
                # For company_id == 4, use YYYYMMDD format for receipts
                prefix = f"REC{bangkok_time.strftime('%Y%m%d')}"
            else:
                prefix = f"{self_prefix}{bangkok_time.strftime('%Y%m')}{currentDate}"

        elif str(self_prefix).startswith("QO") or str(self_prefix).startswith("SO"):
            if company_id == 4:
                # For company_id == 4, use Buddha Era format: 25YYMMDD
                prefix = f"{self_prefix}{be_year}{currentDate}"
            else:
                prefix = f"{self_prefix}{be_year}{currentDate}"

        else:
            if company_id == 4:
                # For company_id == 4, use Buddha Era format: 25YYMMDD
                prefix = f"{self_prefix}{be_year}{currentDate}"
            else:
                prefix = f"{self_prefix}{be_year}{currentDate}"

        # Update last date
        if company_id == 4 and (str(self_prefix).startswith("REC") or str(self_prefix).startswith("PBNK") or 
                               str(self_prefix).startswith("INV") or str(self_prefix).startswith("QO") or 
                               str(self_prefix).startswith("SO") or 'receipt' in str(self.code).lower() or 
                               'payment' in str(self.code).lower() or str(self.code) == 'account.payment.im'):
            # For company_id == 4, store full date (YYYYMMDD) for daily reset
            self.x_studio_last_date = bangkok_time.strftime('%Y%m%d')
        else:
            # For other cases, store day only
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
        _logger.warning(f"=== SEQUENCE DEBUG === next_by_code called with code: '{code}', company_id: {company_id}")
        _logger.warning(f"Company name: {self.env.company.name}")
        
        sequence_code = code
        if company_id == 2:
            sequence_code = sequence_code + '.h3c'
        elif company_id == 4:
            sequence_code = sequence_code + '.im'

        _logger.warning(f"Final sequence_code: '{sequence_code}'")

        sequence = self.search([('code', '=', sequence_code)], limit=1)
        _logger.warning(f"Found sequence: {sequence} with prefix: '{sequence.prefix if sequence else 'N/A'}'")
        
        if sequence:
            # Call _get_prefix_suffix to update number_next if needed
            sequence._get_prefix_suffix()

            # Call the original next_by_code to get the next number
            next_number = super(CustomSequence, sequence).next_by_code(sequence_code, **kwargs)
            _logger.warning(f"Generated next_number: '{next_number}'")

            # Combine the prefix and next number to form the full sequence value
            # prefix, _ = sequence._get_prefix_suffix()  # Get the updated prefix
            return f"{next_number}"  # Adjust as needed

        # Handle case where sequence is not found
        _logger.warning(f"Sequence not found, using default")
        return super(CustomSequence, self).next_by_code(sequence_code, **kwargs)
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
        Override to customize the sequence prefix and suffix. 1
        """

        if self.code in (None, "", False):
            prefix, suffix = super()._get_prefix_suffix()
            return prefix, suffix
        # Call the super method to get the default prefix and suffix
        # Get the current UTC time
        utc_now = datetime.utcnow()

        # Bangkok is UTC+7
        bangkok_time = utc_now + timedelta(hours=7)

        currentDate = bangkok_time.strftime("%d")
        company_id = self.env.context.get('company_id', self.env.company.id)
        _logger.info(f"Sequnece of Company: {company_id}")
        sequence_code = self.code
        if company_id == 2:
            sequence_code = sequence_code + '.h3c'
        # invoice = self.search([('code', '=', 'account.move')], limit=1)
        _logger.info(f"Sequnece Entry: {sequence_code} {self.number_next} | {bangkok_time} {currentDate} {self.x_studio_last_date}")
    
        if currentDate != self.x_studio_last_date:
            sequence = self.search([('code', '=', sequence_code)], limit=1)
            sequence.number_next = 1

        prefix, suffix = super()._get_prefix_suffix()
        # next_by_code = super().next_by_code(self.code)
        # _logger.info(f"Sequnece Entry: {next_by_code}")
        be_year = self._get_buddha_era_year()

        # Optionally modify the prefix
        if self.prefix.startswith("SQ"):
            prefix = f"{self.prefix}{be_year}{currentDate}"
        elif self.prefix.startswith("INV"):
            prefix = f"{self.prefix}{bangkok_time.strftime('%y')}{currentDate}"
        else:
            prefix = f"{self.prefix}{be_year}{currentDate}"

        self.x_studio_last_date = currentDate
        # self.number_next = 1
        # prefix = f"{self.code}{be_year}"
        # Customize the suffix
        # For example, include the Buddha Era year in the suffix
      
        # suffix = f"{be_year}/{suffix}" if suffix else f"{be_year}"
        _logger.info(f"Sequnece Entry: {sequence_code} {self.number_next} | {bangkok_time} {currentDate} {self.x_studio_last_date} {prefix} {suffix}")

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
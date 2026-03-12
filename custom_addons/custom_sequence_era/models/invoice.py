from odoo import models, api
from datetime import datetime, timedelta
import logging
_logger = logging.getLogger(__name__)

class CustomInvoice(models.Model):
    _inherit = 'account.move'

    @api.model
    def create(self, vals):
        _logger.info(f"Invoice Code: {vals}")
        move_type = vals.get('move_type', '')
        
        if move_type == 'out_invoice':
            # Use your custom sequence logic
            if vals.get('state') == 'draft':
                vals['name'] = 'Draft'  # Set the name to "Draft" for draft invoices
            else:
                vals['name'] = self.env['ir.sequence'].next_by_code('account.move')
        elif move_type == 'in_invoice':
            # Use your custom sequence logic
            if vals.get('state') == 'draft':
                vals['name'] = 'Draft'  # Set the name to "Draft" for draft invoices
            else:
                vals['name'] = self.env['ir.sequence'].next_by_code('account.bill.move')

        return super(CustomInvoice, self).create(vals)


class CustomPayment(models.Model):
    _inherit = 'account.payment'

    def _compute_name(self):
        """Override the name computation for company_id == 4"""
        for payment in self:
            if payment.company_id.id == 4:
                # Generate custom sequence for company_id == 4
                utc_now = datetime.utcnow()
                bangkok_time = utc_now + timedelta(hours=7)
                
                # Calculate Buddha Era year (2 digits)
                current_year = bangkok_time.year
                be_year = current_year + 543
                be_year_2digit = str(be_year)[2:4]  # Get last 2 digits (69 from 2569)
                
                month = bangkok_time.strftime('%m')
                day = bangkok_time.strftime('%d')
                date_prefix = f"{be_year_2digit}{month}{day}"
                
                # Find the next number for today
                existing_payments = self.search([
                    ('name', 'like', f'REC{date_prefix}%'),
                    ('company_id', '=', payment.company_id.id),
                    ('id', '!=', payment.id)
                ])
                
                next_number = len(existing_payments) + 1
                payment.name = f"REC{date_prefix}{str(next_number).zfill(2)}"
                _logger.warning(f"Custom _compute_name: {payment.name}")
            else:
                # Use default computation for other companies
                super(CustomPayment, payment)._compute_name()

    @api.model
    def create(self, vals):
        _logger.warning(f"=== PAYMENT DEBUG === Payment create called with vals: {vals}")
        
        company_id = vals.get('company_id') or self.env.company.id
        _logger.warning(f"Payment company_id: {company_id}")
        
        # Don't set name in vals, let _compute_name handle it
        if company_id == 4:
            vals.pop('name', None)  # Remove name if exists
            _logger.warning("Removed name from vals, will use _compute_name")

        result = super(CustomPayment, self).create(vals)
        _logger.warning(f"Created payment with name: {result.name}")
        
        return result
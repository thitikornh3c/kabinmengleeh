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

    @api.model
    def create(self, vals):
        _logger.warning(f"=== PAYMENT DEBUG === Payment create called with vals: {vals}")
        
        company_id = vals.get('company_id') or self.env.company.id
        _logger.warning(f"Payment company_id: {company_id}")
        
        # Generate custom sequence for company_id == 4
        if company_id == 4 and (not vals.get('name') or vals.get('name') == '/' or vals.get('name') == 'New'):
            # Get Bangkok timezone timestamp
            utc_now = datetime.utcnow()
            bangkok_time = utc_now + timedelta(hours=7)
            current_date = bangkok_time.strftime('%Y%m%d')
            
            # Find the next number for today
            existing_payments = self.search([
                ('name', 'like', f'REC{current_date}%'),
                ('company_id', '=', company_id)
            ])
            
            next_number = len(existing_payments) + 1
            custom_name = f"REC{current_date}{str(next_number).zfill(2)}"
            vals['name'] = custom_name
            _logger.warning(f"Generated payment name: {custom_name}")

        result = super(CustomPayment, self).create(vals)
        
        # Force update name after creation if needed
        if result.company_id.id == 4 and (result.name.startswith('PBNK') or '/' in result.name):
            utc_now = datetime.utcnow()
            bangkok_time = utc_now + timedelta(hours=7)
            current_date = bangkok_time.strftime('%Y%m%d')
            
            existing_payments = self.search([
                ('name', 'like', f'REC{current_date}%'),
                ('company_id', '=', result.company_id.id),
                ('id', '!=', result.id)
            ])
            
            next_number = len(existing_payments) + 1
            custom_name = f"REC{current_date}{str(next_number).zfill(2)}"
            result.name = custom_name
            _logger.warning(f"Force updated payment name to: {custom_name}")
        
        return result

    def write(self, vals):
        # Prevent name from being overwritten by sequence
        if self.company_id.id == 4 and 'name' in vals and vals['name'] and vals['name'].startswith('PBNK'):
            utc_now = datetime.utcnow()
            bangkok_time = utc_now + timedelta(hours=7)
            current_date = bangkok_time.strftime('%Y%m%d')
            
            existing_payments = self.search([
                ('name', 'like', f'REC{current_date}%'),
                ('company_id', '=', self.company_id.id),
                ('id', '!=', self.id)
            ])
            
            next_number = len(existing_payments) + 1
            vals['name'] = f"REC{current_date}{str(next_number).zfill(2)}"
            _logger.warning(f"Prevented PBNK override, using: {vals['name']}")
        
        return super(CustomPayment, self).write(vals)
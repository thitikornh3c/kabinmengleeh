import requests
from odoo import models, fields, api
from datetime import datetime
import io
import csv

class AccountPND53Report(models.Model):
    _inherit = 'account.report'

    def action_export_pnd53_pdf(self):
        self.ensure_one()
        if self.name != 'PND53':
            return

        today = datetime.today()
        month = self._context.get('pnd53_month', today.month)
        year = self._context.get('pnd53_year', today.year)

        options = self.get_options({
            'date': {
                'date_from': f'{year}-{month:02d}-01',
                'date_to': f'{year}-{month:02d}-31',  # adjust for month end if needed
            }
        })
        lines = self._get_lines(options)

        # Build CSV with exact required columns
        csv_file = io.StringIO()
        writer = csv.writer(csv_file)
        writer.writerow([
            'No.', 'Tax ID', 'Title', 'Contact Name', 'Street', 'Street2', 'City', 'State', 'Zip',
            'Branch Number', 'Invoice/Bill Date', 'Tax Rate', 'Total Amount', 'WHT Amount',
            'WHT Condition', 'Tax Type'
        ])

        for i, line in enumerate(lines, start=1):
            partner = line.get('partner', {})
            writer.writerow([
                i,
                partner.get('vat', ''),
                partner.get('company_type', ''),  # Title
                partner.get('name', ''),          # Contact Name
                partner.get('street', ''),
                partner.get('street2', ''),
                partner.get('city', ''),
                partner.get('state_id', {}).get('name', ''),
                partner.get('zip', ''),
                partner.get('branch_no', ''),     # if custom field
                line.get('date', ''),
                ','.join([str(t.get('amount', '')) for t in line.get('taxes', [])]),  # Tax Rate
                line.get('balance', 0.0),         # Total Amount
                line.get('wht_amount', 0.0),     # WHT Amount (if available)
                line.get('wht_condition', ''),   # WHT Condition (if available)
                line.get('tax_type', 'Service')  # Tax Type
            ])

        csv_content = csv_file.getvalue()

        url = "https://odoo.h3creation.com/api/v1/account/pnd53/print"
        files = {"file": ("pnd53.csv", csv_content, "text/csv")}
        try:
            response = requests.post(url, files=files, timeout=30)
            response.raise_for_status()
            data = response.json()
            paths = data.get('paths', [])
        except Exception as e:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Error',
                    'message': f'Failed to export PND53: {str(e)}',
                    'type': 'danger'
                }
            }

        base_url = "https://odoo.h3creation.com"
        link_text = "<br/>".join([f'<a href="{base_url}{p}" target="_blank">{p.split("/")[-1]}</a>' for p in paths])

        return {
            'type': 'ir.actions.act_window',
            'name': 'PND53 PDF Links',
            'res_model': 'pnd53.message.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_message': link_text}
        }


class PND53MessageWizard(models.TransientModel):
    _name = "pnd53.message.wizard"
    _description = "Display PDF links"

    message = fields.Text(
        string="Message",
        readonly=True,
        default=lambda self: self._context.get("default_message", "")
    )

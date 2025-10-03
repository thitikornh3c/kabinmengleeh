import requests
from odoo import models, fields, api
from datetime import datetime
import io
import csv
import logging
_logger = logging.getLogger(__name__)

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
                'date_from': f'2025-09-01',
                'date_to': f'2025-09-30',  # adjust for month end if needed
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
            move = line.get('move_id')
            partner = move.partner_id if move else None

            writer.writerow([
                i,
                partner.vat if partner else '',
                partner.company_type if partner else '',
                partner.name if partner else '',
                partner.street if partner else '',
                partner.street2 if partner else '',
                partner.city if partner else '',
                partner.state_id.name if partner and partner.state_id else '',
                partner.zip if partner else '',
                getattr(partner, 'branch_no', '') if partner else '',
                move.date if move else '',
                ','.join([str(t.amount) for t in move.tax_line_ids]) if move else '',
                line.get('balance', 0.0),
                getattr(move, 'wht_amount', 0.0),
                getattr(move, 'wht_condition', ''),
                getattr(move, 'tax_type', 'Service')
            ])

        csv_content = csv_file.getvalue()
        _logger.info(f"Content {csv_content}")
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

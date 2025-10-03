import requests
from odoo import models, fields, api

class AccountPND53(models.Model):
    _inherit = 'account.report'
    
    @api.model
    def action_export_pnd53_pdf(self):
        # Search PND53 report
        report = self.search([('name', '=', 'PND53')], limit=1)
        if not report:
            return {'warning': 'PND53 report not found'}

        # Get default options (you can customize date filters)
        options = report._get_options({})

        # Get lines
        lines = report._get_lines(options)

        # Convert lines to CSV
        csv_rows = []
        for line in lines:
            csv_rows.append([line.get('name', ''), line.get('balance', 0)])
        csv_content = "\n".join([",".join(map(str, row)) for row in csv_rows])

        # Send CSV to Node.js API
        url = "http://your-node-server/api/v1/account/pnd53/print"
        files = {"file": ("pnd53.csv", csv_content, "text/csv")}
        try:
            response = requests.post(url, files=files, timeout=30)
            response.raise_for_status()
            links = response.json()  # expect ["link.pdf", ...]
        except Exception as e:
            return {'warning': f'Failed to send CSV to API: {str(e)}'}

        # Return download links to user
        link_text = "\n".join(links)
        return {
            'type': 'ir.actions.act_window',
            'name': 'PND53 PDF Links',
            'res_model': 'ir.actions.act_window.message',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_message': link_text
            }
        }
class MessageWizard(models.TransientModel):
    _name = 'ir.actions.act_window.message'
    _description = 'Display links message'

    message = fields.Text('Message', readonly=True, default=lambda self: self._context.get('default_message', ''))
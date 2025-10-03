import requests
from odoo import models, fields, api

class AccountPND53(models.Model):
    _inherit = 'account.report'

    @api.model
    def action_export_pnd53_pdf(self):
        report = self.search([('name', '=', 'PND53')], limit=1)
        if not report:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Warning',
                    'message': 'PND53 report not found',
                    'type': 'warning'
                }
            }

        options = report._get_options({})
        lines = report._get_lines(options)

        csv_rows = [[line.get('name', ''), line.get('balance', 0)] for line in lines]
        csv_content = "\n".join([",".join(map(str, row)) for row in csv_rows])

        url = "http://your-node-server/api/v1/account/pnd53/print"
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
                    'message': f'Failed to send CSV to API: {str(e)}',
                    'type': 'danger'
                }
            }

        # Build clickable HTML links
        base_url = "http://your-node-server"  # replace with your actual server URL
        link_text = "<br/>".join([f'<a href="{base_url}{p}" target="_blank">{p.split("/")[-1]}</a>' for p in paths])

        return {
            'type': 'ir.actions.act_window',
            'name': 'PND53 PDF Links',
            'res_model': 'pnd53.message.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_message': link_text}
        }

class MessageWizard(models.TransientModel):
    _name = 'pnd53.message.wizard'
    _description = 'Display links message'

    message = fields.Text('Message', readonly=True, default=lambda self: self._context.get('default_message', ''))

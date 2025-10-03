import requests
from odoo import models, fields, api
from datetime import datetime

class AccountPND53Report(models.Model):
    _inherit = 'account.report'

    def action_export_pnd53_pdf(self):
        self.ensure_one()

        if self.name != 'PND53':
            return

        today = datetime.today()
        month = self._context.get('pnd53_month', today.month)
        year = self._context.get('pnd53_year', today.year)

        options = self._get_options({'date': f'{year}-{month:02d}-01'})
        lines = self._get_lines(options)

        csv_rows = [[line.get('name', ''), line.get('balance', 0)] for line in lines]
        csv_content = "\n".join([",".join(map(str, row)) for row in csv_rows])

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

        base_url = "https://odoo.h3creation.com"  # replace with your actual server URL
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
# import requests
# from odoo import models, fields, api

# class AccountPND53(models.Model):
#     _inherit = 'account.report'

#     name = fields.Char('Description')
#     date = fields.Date('Date')

#     @api.model
#     def action_export_pnd53_pdf(self):
#         report = self.search([('name', '=', 'PND53')], limit=1)
#         if not report:
#             return {
#                 'type': 'ir.actions.client',
#                 'tag': 'display_notification',
#                 'params': {
#                     'title': 'Warning',
#                     'message': 'PND53 report not found',
#                     'type': 'warning'
#                 }
#             }

#         options = report._get_options({})
#         lines = report._get_lines(options)

#         csv_rows = [[line.get('name', ''), line.get('balance', 0)] for line in lines]
#         csv_content = "\n".join([",".join(map(str, row)) for row in csv_rows])

#         url = "http://your-node-server/api/v1/account/pnd53/print"
#         files = {"file": ("pnd53.csv", csv_content, "text/csv")}
#         try:
#             response = requests.post(url, files=files, timeout=30)
#             response.raise_for_status()
#             data = response.json()
#             paths = data.get('paths', [])
#         except Exception as e:
#             return {
#                 'type': 'ir.actions.client',
#                 'tag': 'display_notification',
#                 'params': {
#                     'title': 'Error',
#                     'message': f'Failed to send CSV to API: {str(e)}',
#                     'type': 'danger'
#                 }
#             }

#         # Build clickable HTML links
#         base_url = "http://your-node-server"  # replace with your actual server URL
#         link_text = "<br/>".join([f'<a href="{base_url}{p}" target="_blank">{p.split("/")[-1]}</a>' for p in paths])

#         return {
#             'type': 'ir.actions.act_window',
#             'name': 'PND53 PDF Links',
#             'res_model': 'pnd53.message.wizard',
#             'view_mode': 'form',
#             'target': 'new',
#             'context': {'default_message': link_text}
#         }

# class MessageWizard(models.TransientModel):
#     _name = 'pnd53.message.wizard'
#     _description = 'Display links message'

#     message = fields.Text('Message', readonly=True, default=lambda self: self._context.get('default_message', ''))

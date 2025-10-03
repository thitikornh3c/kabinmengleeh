import requests
from odoo import models, api

class AccountPND53(models.Model):
    _inherit = "l10n_th_pnd.wizard.pnd53"
    
    @api.model
    def action_export_pnd53_pdf(self):
        # Get CSV content using same Odoo wizard method
        content, filename = self._get_content('csv')   # just like l10n_ar_withholding
        # or: content = self._get_csv()

        if isinstance(content, bytes):
            content = content.decode("utf-8")

        files = {"file": (filename or "pnd53.csv", content, "text/csv")}
        url = "https://https://odoo.h3creation.com/api/v1/account/pnd53/print"

        response = requests.post(url, files=files, timeout=60)
        response.raise_for_status()
        links = response.json()

        return {
            "type": "ir.actions.client",
            "tag": "download_pnd53_pdf",
            "params": {"links": links},
        }
        # """
        # Export current PND53/PND3 as CSV, send to Node.js API, 
        # and return PDF download links.
        # """
        # # Example: normally you generate CSV using existing method
        # file_content = "your,csv,content\nrow,1,2,3\n"

        # files = {"file": ("pnd53.csv", file_content, "text/csv")}

        # url = "https://https://odoo.h3creation.com/api/v1/account/pnd53/print"
        # response = requests.post(url, files=files, timeout=60)
        # response.raise_for_status()

        # links = response.json()  # ["link1.pdf", "link2.pdf"]

        # return {
        #     "type": "ir.actions.client",
        #     "tag": "download_pnd53_pdf",
        #     "params": {"links": links},
        # }

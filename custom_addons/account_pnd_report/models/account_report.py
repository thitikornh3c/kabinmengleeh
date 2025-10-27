import requests
from odoo import models, fields, api, _
from datetime import datetime
import io
import csv
import logging
_logger = logging.getLogger(__name__)

class AccountPNDReport(models.Model):
    _inherit = 'account.report'

    def action_export_pnd53_pdf(self):
        # This method is called by the old server action in your manifest. 
        # Since we are using a direct wizard call from the menu, 
        # this code path is deprecated but kept minimal for backward compatibility if needed.
        return {
            'type': 'ir.actions.act_window',
            'name': _('Export PND'),
            'res_model': 'pnd53.export.wizard',
            'view_mode': 'form',
            'target': 'new',
        }


# *** FIX FOR MODEL NOT FOUND ERROR ***
# The view pnd53_message_wizard_view.xml requires this model to exist.
class AccountPNDMessageWizard(models.TransientModel):
    _name = "account.pnd.message.wizard"
    _description = "Display PND Report PDF links"

    message = fields.Html(
        string="Message",
        readonly=True,
    )


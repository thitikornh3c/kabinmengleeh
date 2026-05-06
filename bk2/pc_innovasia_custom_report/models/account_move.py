from odoo import models, fields

class AccountMove(models.Model):
    _inherit = "account.move"

    pc_remittance_info = fields.Html(
        string="Remittance Info",
        store=True,
    )
    pc_show_remittance_info = fields.Boolean(
        string="Show Remittance Info in printed PDF?",
        store=True,
    )
    pc_show_narration = fields.Boolean(
        string="Show Terms and Conditions",
        store=True,
    )

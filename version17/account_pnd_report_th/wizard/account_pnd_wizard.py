from odoo import models, fields
from datetime import date


class AccountPNDWizard(models.TransientModel):
    _name = 'account.pnd.wizard'
    _description = 'PND 3/53 Wizard'

    pnd_type = fields.Selection([
        ('pnd3', 'PND3'),
        ('pnd53', 'PND53')
    ], required=True, string="Form Type", default='pnd53')

    date_start = fields.Date(string="Start Date", required=True,
                             default=lambda self: date.today().replace(day=1))
    date_end = fields.Date(string="End Date", required=True, default=lambda self: date.today())

    def action_generate_pnd(self):
        self.ensure_one()
        return self.env['account.pnd.report'].generate_pnd_reports(self)

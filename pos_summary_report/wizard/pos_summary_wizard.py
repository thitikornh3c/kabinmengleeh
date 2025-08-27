from odoo import models, fields
from datetime import datetime, time

class PosSummaryWizard(models.TransientModel):
    _name = "pos.summary.wizard"
    _description = "POS Sales Summary Wizard"

    config_ids = fields.Many2many("pos.config", string="POS Configurations")
    date_from = fields.Date(string="From", required=True, default=fields.Date.context_today)
    date_to = fields.Date(string="To", required=True, default=fields.Date.context_today)

    def action_print(self):
        self.ensure_one()
        dt_from = datetime.combine(self.date_from, time.min)
        dt_to = datetime.combine(self.date_to, time.max)
        data = {
            "date_from": dt_from.strftime("%Y-%m-%d %H:%M:%S"),
            "date_to": dt_to.strftime("%Y-%m-%d %H:%M:%S"),
            "config_ids": self.config_ids.ids,
        }
        return self.env.ref("pos_summary_report.action_pos_summary_report").report_action(None, data=data)

        # return self.env.ref("pos_summary_report2.action_pos_summary_report").report_action(None, data=data)
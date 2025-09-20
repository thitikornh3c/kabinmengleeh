from odoo import models, api
import logging

_logger = logging.getLogger(__name__)

class HrWorkEntry(models.Model):
    _inherit = 'hr.attendance.log'

    @api.model
    def clear_validated_entries(self):
        validated_entries = self.filtered(lambda e: e.state == 'validated')
        for entry in validated_entries:
            entry.sudo().write({'state': 'draft'})
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': "Success",
                'message': f"{len(validated_entries)} attendances reverted to draft.",
                'type': 'success',
                'sticky': False,
            }
        }
    
    # _inherit = 'hr.work.entry'

    # @api.model
    # def clear_validated_entries(self):
    #     validated_entries = self.filtered(lambda e: e.state == 'validated')
    #     for entry in validated_entries:
    #         entry.sudo().write({'state': 'draft'})
    #     _logger.info(f"{len(validated_entries)} selected work entries reverted to draft.")
    #     return {
    #         'type': 'ir.actions.client',
    #         'tag': 'display_notification',
    #         'params': {
    #             'title': "Success",
    #             'message': f"{len(validated_entries)} work entries reverted to draft.",
    #             'type': 'success',
    #             'sticky': False,
    #         }
    #     }
from odoo import models, fields, api

class MergePOSOrdersWizard(models.TransientModel):
    _name = 'merge.pos.orders.wizard'
    _description = 'Merge POS Orders Wizard'

    pos_order_ids = fields.Many2many('pos.order', string="POS Orders")

    def action_merge_and_invoice(self):
        invoice = self.pos_order_ids._merge_and_create_invoice()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Invoice',
            'res_model': 'account.move',
            'res_id': invoice.id,
            'view_mode': 'form',
            'target': 'current',
        }

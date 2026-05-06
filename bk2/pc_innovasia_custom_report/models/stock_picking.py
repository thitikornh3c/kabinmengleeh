from odoo import fields, models

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    pc_show_price_on_report = fields.Boolean(
        string="Show Price on Report", 
        store=True,
        help="To show the Price on the Packing List PDF print")
    pc_show_sign_stamp = fields.Boolean(
        string="Show Sign and Stamp on PDF",
    )
    pc_sign_by = fields.Many2one("res.users", string="Signed By")

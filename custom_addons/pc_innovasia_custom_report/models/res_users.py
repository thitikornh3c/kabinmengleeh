from odoo import fields, models, _


class ResUsers(models.Model):
    _inherit = "res.users"

    pc_user_signature = fields.Image(
        string="User Signature",
        copy=False, attachment=True, max_width=1024, max_height=1024)

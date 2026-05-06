from odoo import fields, models

class ResCompany(models.Model):
    _inherit = "res.company"

    pc_local_address = fields.Html(
        string="Local Address",
        store=True,
        help="Enter your company’s address in your local language here. This address will be displayed in the PDF reports."
    )
    pc_company_stamp = fields.Image(
        string="Company Stamp",
        copy=False, attachment=True, max_width=1024, max_height=1024)
    
    pc_show_packing_list_as_do = fields.Boolean(
        string="Show Packing List as Delivery Order",
        store=True,
        help="Check this box to display 'Delivery Order' instead of 'Packing List' on documents."
    )

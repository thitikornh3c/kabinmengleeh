# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Gayathri V (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
################################################################################
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    """Add new fields to display service products"""
    _inherit = 'res.config.settings'

    interest_product_id = fields.Many2one('product.product',
                                          string="Interest Product",
                                          help="Product For Interest "
                                               "To Create Invoice Lines")
    repayment_product_id = fields.Many2one('product.product',
                                           string="Repayment Product",
                                           help="Product For Repayment "
                                                "To Create Invoice Lines")

    def get_values(self):
        res = super().get_values()
        params = self.env['ir.config_parameter'].sudo()
        interest_id = params.get_param('advanced_loan_management.interest_product_id')
        repayment_id = params.get_param('advanced_loan_management.repayment_product_id')
        res.update(
            interest_product_id=int(interest_id) if interest_id else False,
            repayment_product_id=int(repayment_id) if repayment_id else False,
        )
        return res

    def set_values(self):
        super().set_values()
        params = self.env['ir.config_parameter'].sudo()
        params.set_param('advanced_loan_management.interest_product_id',
                         self.interest_product_id.id or False)
        params.set_param('advanced_loan_management.repayment_product_id',
                         self.repayment_product_id.id or False)

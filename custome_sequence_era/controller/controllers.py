# -*- coding: utf-8 -*-
# from odoo import http


# class CustomSequenceEra(http.Controller):
#     @http.route('/custom_sequence_era/custom_sequence_era', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/custom_sequence_era/custom_sequence_era/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('custom_sequence_era.listing', {
#             'root': '/custom_sequence_era/custom_sequence_era',
#             'objects': http.request.env['custom_sequence_era.custom_sequence_era'].search([]),
#         })

#     @http.route('/custom_sequence_era/custom_sequence_era/objects/<model("custom_sequence_era.custom_sequence_era"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('custom_sequence_era.object', {
#             'object': obj
#         })


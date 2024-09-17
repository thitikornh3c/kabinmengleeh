# -*- coding: utf-8 -*-
# from odoo import http


# class LoanManagement(http.Controller):
#     @http.route('/loan_management/loan_management', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/loan_management/loan_management/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('loan_management.listing', {
#             'root': '/loan_management/loan_management',
#             'objects': http.request.env['loan_management.loan_management'].search([]),
#         })

#     @http.route('/loan_management/loan_management/objects/<model("loan_management.loan_management"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('loan_management.object', {
#             'object': obj
#         })


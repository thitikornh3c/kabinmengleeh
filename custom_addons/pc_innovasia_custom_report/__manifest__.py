{
    'name': 'Innovasia Custom Report',
    "version": "18.0.1.0.0",
    'summary': ' Innovasia Custom Report',
    "description": """
Change Log
Version 1.0.0 (October 3rd, 2024)
* Add new Custom Report template
        """,
    'category': 'Sale, Report',
    'author': 'Portcities',
    'website': 'https://www.portcities.net/',
    'license': 'LGPL-3',
    'depends': ['base', 'sale','account'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/paperformat.xml',        
        'reports/layout.xml',
        'reports/report_sale_order.xml',
        'reports/sale_order_report.xml',
        'reports/report_purchase_order.xml',
        'reports/purchase_order_report.xml',
        'reports/report_account_move.xml',
        'reports/account_move_report.xml',
        'reports/delivery_order_report.xml',
        'reports/report_delivery_order.xml',        
        'views/account_move_views.xml',
        'views/stock_picking_views.xml',
        'views/sale_order_views.xml',
        'views/res_company_views.xml',
        'views/res_users_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}

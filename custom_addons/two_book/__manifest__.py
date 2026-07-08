# -*- coding: utf-8 -*-
{
    'name': 'Two Book - VAT & Non-VAT Sales (Thailand)',
    'version': '19.0.1.5.9',
    'category': 'Accounting/Accounting',
    'summary': 'รองรับการขายแบบ Hybrid: ใบกำกับภาษีเต็มรูป และบิลเงินสด (Non-VAT) สำหรับร้านวัสดุก่อสร้างไทย',
    'description': """
        Two Book Module
        ===============
        - แยกการขายเป็น 2 ประเภท: VAT (ใบกำกับภาษี) และ Non-VAT (บิลเงินสด)
        - Dual-Stock: ตัด WH/Stock ทุกบิล + ตัด WH/VAT เฉพาะ VAT
        - Stock Gap report + reconcile wizard
        - แยก Journal ตอนปิด session (VAT / Non-VAT)
        - รายงานสรุปยอดแยก VAT / Non-VAT สำหรับ ภ.พ.30
    """,
    'author': 'Custom',
    'depends': ['point_of_sale', 'account', 'stock', 'pos_merge_invoice'],
    'data': [
        'security/ir.model.access.csv',
        'data/account_data.xml',
        'data/stock_data.xml',
        'views/pos_config_view.xml',
        'views/pos_order_view.xml',
        'views/stock_gap_views.xml',
        'wizard/stock_gap_reconcile_wizard_view.xml',
        'wizard/two_book_pp30_wizard_views.xml',
        'report/two_book_report.xml',
        'data/two_book_pp30_menu.xml',
        'report/two_book_pp30_report.xml',
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'two_book/static/src/scss/two_book.scss',
            'two_book/static/src/js/two_book_pos_order.js',
            'two_book/static/src/js/two_book_button.js',
            'two_book/static/src/js/two_book_actionpad.js',
            'two_book/static/src/xml/two_book_button.xml',
        ],
    },
    'post_init_hook': 'post_init_hook',
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}

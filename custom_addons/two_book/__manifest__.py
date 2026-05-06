# -*- coding: utf-8 -*-
{
    'name': 'Two Book - VAT & Non-VAT Sales (Thailand)',
    'version': '18.0.1.0.0',
    'category': 'Accounting/Accounting',
    'summary': 'รองรับการขายแบบ Hybrid: ใบกำกับภาษีเต็มรูป และบิลเงินสด (Non-VAT) สำหรับร้านวัสดุก่อสร้างไทย',
    'description': """
        Two Book Module
        ===============
        - แยกการขายเป็น 2 ประเภท: VAT (ใบกำกับภาษี) และ Non-VAT (บิลเงินสด)
        - ตัด Stock ทุกรายการไม่ว่าจะออกใบกำกับหรือไม่
        - แยก Journal Entry อัตโนมัติตามประเภทการขาย
        - รายงานสรุปยอดแยก VAT / Non-VAT สำหรับ ภ.พ.30
    """,
    'author': 'Custom',
    'depends': ['point_of_sale', 'account', 'stock'],
    'data': [
        'security/ir.model.access.csv',
        'data/account_data.xml',
        'views/pos_config_view.xml',
        'views/pos_order_view.xml',
        'report/two_book_report.xml',
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'two_book/static/src/js/two_book_button.js',
            'two_book/static/src/xml/two_book_button.xml',
        ],
    },
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}

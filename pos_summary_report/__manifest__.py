{
    "name": "POS Sales Summary Styled Report by H3C",
    "version": "17.0.1.1.0",
    "summary": "Daily POS summary styled like Sales Details",
    "category": "Point of Sale",
    "author": "ChatGPT",
    "depends": ["point_of_sale"],
    'data': [
        'security/ir.model.access.csv',
        'report/pos_summary_report.xml',
        'report/pos_summary_report_templates.xml',
        'wizard/pos_summary_wizard_views.xml'
    ],
    'installable': True,
    'application': False,
}
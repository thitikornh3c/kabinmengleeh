{
    'name': 'Thai PND 3/53 Report Generator',
    'version': '1.0',
    'category': 'Accounting',
    'summary': 'Generate Thai PND3 and PND53 forms from accounting transactions',
    'author': 'Your Company',
    'depends': ['base', 'account'],
    'data': [
        'security/ir.model.access.csv',
        'views/pnd_wizard_view.xml',
        'views/pnd_menu.xml',
        'views/pnd_result_view.xml',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'application': False,
}
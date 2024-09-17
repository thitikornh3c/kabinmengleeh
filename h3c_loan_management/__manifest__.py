{
    'name': 'Kabin Loan Management',
    'version': '1.0',
    'category': 'Accounting',
    'summary': 'Manage employee loans and payroll deductions',
    'description': 'Module for managing loans, installments, and payroll deductions',
    'author': 'Your Name',
    'depends': ['base', 'hr_payroll'],
    'data': [
        'security/ir.model.access.csv',
        'views/loan_views.xml',
        'views/payroll_views.xml',
    ],
    'icon': '/loan_management/static/description/icon.png',
    'installable': True,
    'application': True,
}
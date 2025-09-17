{
    "name": "POS Merge Orders to Invoice",
    "version": "18.0.1.0.0",
    "category": "Point of Sale",
    "summary": "Merge multiple POS orders into one invoice",
    "depends": ["point_of_sale", "account"],
    'author': 'Happy Three Creation',
    "data": [
        'security/ir.model.access.csv',
        "views/merge_wizard_view.xml",
        "views/pos_order_action.xml"
    ],
    "installable": True,
    "application": False,
}
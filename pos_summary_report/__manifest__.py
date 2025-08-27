{
    "name": "POS Sales Summary Styled Report by H3C",
    "version": "17.0.1.1.0",
    "summary": "Daily POS summary styled like Sales Details",
    "category": "Point of Sale",
    "author": "ChatGPT",
    "depends": ["point_of_sale"],
    "data": [
        "security/ir.model.access.csv",
        "views/pos_summary_wizard_view.xml",
        "report/pos_summary_report.xml",
        "report/pos_summary_report_templates.xml"
    ],
    "license": "LGPL-3",
    "installable": True,
    "application": False
}
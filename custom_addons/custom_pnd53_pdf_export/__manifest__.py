{
    "name": "H3C PND53 PDF Export",
    "version": "1.0",
    "depends": ["base", "account"],
    "author": "Your Name",
    "category": "Accounting",
    "summary": "Add Export PDF button for PND53 / PND3 using external API",
    "data": [
        "security/ir.model.access.csv",
        # "views/account_pnd53_menu.xml",
        "views/account_pnd53_button_view.xml", # Now launches the wizard action
        "views/pnd53_export_wizard_view.xml",  # NEW DATE WIZARD VIEW
        "views/pnd53_message_wizard_view.xml", # Kept for backward compatibility
    ],
    # "assets": {
    #     "web.assets_backend": [
    #         "custom_pnd53_pdf_export/static/src/js/download_pnd53.js",
    #     ],
    # },
    "installable": True,
    "application": False,
}

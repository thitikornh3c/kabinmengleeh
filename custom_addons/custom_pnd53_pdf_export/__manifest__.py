{
    "name": "H3C PND53 PDF Export",
    "version": "1.0",
    "depends": ["base", "account"],
    "author": "Your Name",
    "category": "Accounting",
    "summary": "Add Export PDF button for PND53 / PND3 using external API",
    "data": [
        "views/account_pnd53_button_view.xml",
        "views/pnd53_message_wizard_view.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "custom_pnd53_pdf_export/static/src/js/download_pnd53.js",
        ],
    },
    "installable": True,
    "application": False,
}

{
    "name": "Account PND Report Export", # Revised module name
    "version": "1.0",
    "depends": ["base", "account"],
    "author": "Happy Three Creation co., ltd.",
    'website': 'https://www.h3creation.com/',
    "category": "Accounting",
    "summary": "Add Export PDF button for PND Report (PND53/PND3) using external API",
    "data": [
        "security/ir.model.access.csv",
        # FILE NAMES RENAMED
        "views/account_pnd_export_wizard_view.xml",  
        "views/account_pnd_button_view.xml",
        "views/account_pnd_menu.xml",
        "views/account_pnd_message_wizard_view.xml",
    ],
    # If using assets, update the folder name here:
    # "assets": {
    #     "web.assets_backend": [
    #         "account_pnd_report/static/src/js/download_pnd53.js", 
    #     ],
    # },
    "installable": True,
    "application": False,
}
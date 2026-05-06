def migrate(cr, version):
    # Remove incompatible view from Odoo 18 that breaks Odoo 19 module loading
    cr.execute("""
        DELETE FROM ir_model_data
        WHERE model = 'ir.ui.view'
          AND name = 'report_invoice_document_preview'
    """)
    cr.execute("""
        DELETE FROM ir_ui_view
        WHERE key = 'account.report_invoice_document_preview'
    """)

    # Fix tax_tag_invert inconsistency for +Income PND53 on customer invoices
    # out_invoice lines must be False (standard Odoo sales convention)
    cr.execute("""
        UPDATE account_move_line aml
        SET tax_tag_invert = false
        FROM account_account_tag_account_move_line_rel rel,
             account_move am
        WHERE rel.account_move_line_id = aml.id
          AND am.id = aml.move_id
          AND rel.account_account_tag_id = (
              SELECT id FROM account_account_tag
              WHERE name::json->>'en_US' = '+Income PND53'
              LIMIT 1
          )
          AND am.move_type = 'out_invoice'
          AND aml.tax_tag_invert = true
    """)

import os
import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    # Set env var to bypass Odoo tax tag migration check
    # Thai PND53 tags have non-standard setup that causes false-positive failure
    os.environ['ODOO_UPG_IGNORE_TAX_TAGS'] = '1'

    # 1. Remove Odoo 18 view incompatible with Odoo 19 template structure
    cr.execute("DELETE FROM ir_model_data WHERE model = 'ir.ui.view' AND name = 'report_invoice_document_preview'")
    cr.execute("DELETE FROM ir_ui_view WHERE key = 'account.report_invoice_document_preview'")

    # 2. Fix tax_tag_invert: customer invoice lines should be False (Odoo standard)
    cr.execute("""
        UPDATE account_move_line aml
        SET tax_tag_invert = false
        FROM account_account_tag_account_move_line_rel rel, account_move am
        WHERE rel.account_move_line_id = aml.id AND am.id = aml.move_id
          AND rel.account_account_tag_id IN (
              SELECT id FROM account_account_tag
              WHERE name::json->>'en_US' IN ('+Income PND53', '+PND53')
          )
          AND am.move_type = 'out_invoice' AND aml.tax_tag_invert = true
    """)

    # 3. Force link Thai PND tax tags to ir.model.data
    # Odoo 19 migration uses xml_id to identify +/- tag pairs
    tags_to_map = [
        ('+1. Sales amount', 'tax_tag_pnd30_sales_amount_plus'),
        ('-1. Sales amount', 'tax_tag_pnd30_sales_amount_minus'),
        ('+5. Output tax', 'tax_tag_pnd30_output_tax_plus'),
        ('-5. Output tax', 'tax_tag_pnd30_output_tax_minus'),
        ('+Income PND53', 'tax_tag_pnd53_income_plus'),
        ('-Income PND53', 'tax_tag_pnd53_income_minus'),
        ('+PND53', 'tax_tag_pnd53_plus'),
        ('-PND53', 'tax_tag_pnd53_minus'),
        ('+Income PND3', 'tax_tag_pnd3_income_plus'),
        ('-Income PND3', 'tax_tag_pnd3_income_minus'),
        ('+PND3', 'tax_tag_pnd3_plus'),
        ('-PND3', 'tax_tag_pnd3_minus'),
    ]

    for label, xml_id in tags_to_map:
        cr.execute("""
            INSERT INTO ir_model_data (name, module, model, res_id, noupdate)
            SELECT %s, 'l10n_th', 'account.account.tag', id, true
            FROM account_account_tag
            WHERE name::json->>'en_US' = %s
            ON CONFLICT DO NOTHING
        """, (xml_id, label))
        _logger.info("Mapped tax tag '%s' to xml_id l10n_th.%s", label, xml_id)
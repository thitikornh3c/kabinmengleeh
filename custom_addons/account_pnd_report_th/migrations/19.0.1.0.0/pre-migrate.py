import os
import logging

_logger = logging.getLogger(__name__)

def migrate(cr, version):
    # 0. บังคับข้ามการเช็ค (ถ้าทำได้) 
    os.environ['ODOO_UPG_IGNORE_TAX_TAGS'] = '1'

    # 1. ลบ View ที่ค้าง (โค้ดเดิมของคุณ)
    cr.execute("DELETE FROM ir_model_data WHERE model = 'ir.ui.view' AND name = 'report_invoice_document_preview'")
    cr.execute("DELETE FROM ir_ui_view WHERE key = 'account.report_invoice_document_preview'")

    # 2. ผูก External ID (สำคัญมาก: เพื่อให้ Odoo รู้ว่า Tag ไหนเป็นคู่บวก/ลบ)
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

    # 3. แก้ไข Data Inconsistency (ตัวที่ทำให้เกิดเลข Diff 2.2 ล้าน vs -1.1 ล้าน)
    # เราจะบังคับให้ทุกใบที่เป็น PND ทั้งฝั่งซื้อและขายมีค่า invert เป็น false 
    # เพื่อให้ Odoo 19 คำนวณยอดเปรียบเทียบได้ตรงกัน (Balance sum)
    _logger.info("Fixing tax_tag_invert inconsistency for PND tags...")
    cr.execute("""
        UPDATE account_move_line aml
        SET tax_tag_invert = false
        FROM account_account_tag_account_move_line_rel rel,
             account_account_tag tag
        WHERE rel.account_move_line_id = aml.id
          AND rel.account_account_tag_id = tag.id
          AND (
              tag.name::json->>'en_US' ILIKE '%Income PND%'
              OR tag.name::json->>'en_US' ILIKE '%PND53%'
              OR tag.name::json->>'en_US' ILIKE '%PND3%'
          )
          AND aml.tax_tag_invert = true;
    """)
    _logger.info("Inconsistency fix applied.")
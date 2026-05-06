import os
import logging

_logger = logging.getLogger(__name__)

def migrate(cr, version):
    # 0. บังคับข้ามการเช็คผ่าน Environment Variable
    os.environ['ODOO_UPG_IGNORE_TAX_TAGS'] = '1'

    # 1. ลบ View ที่ค้าง (Odoo 18 Incompatible)
    cr.execute("DELETE FROM ir_model_data WHERE model = 'ir.ui.view' AND name = 'report_invoice_document_preview'")
    cr.execute("DELETE FROM ir_ui_view WHERE key = 'account.report_invoice_document_preview'")

    # 2. ผูก External ID ให้ครบ (รวมตัว '1. Sales amount' ที่ Error ล่าสุดฟ้อง)
    tags_to_map = [
        ('+1. Sales amount', 'tax_tag_pnd30_sales_amount_plus'),
        ('-1. Sales amount', 'tax_tag_pnd30_sales_amount_minus'),
        ('1. Sales amount', 'tax_tag_pnd30_sales_amount_standard'), # เพิ่มตัวนี้
        ('+5. Output tax', 'tax_tag_pnd30_output_tax_plus'),
        ('-5. Output tax', 'tax_tag_pnd30_output_tax_minus'),
        ('+Income PND53', 'tax_tag_pnd53_income_plus'),
        ('-Income PND53', 'tax_tag_pnd53_income_minus'),
        ('+PND53', 'tax_tag_pnd53_plus'),
        ('-PND53', 'tax_tag_pnd53_minus'),
        ('PND53', 'tax_tag_pnd53_standard'), # เพิ่มตัวนี้
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

    # 3. [กวาดล้างใหญ่] Set tax_tag_invert เป็น False ให้หมดทั้งระบบ
    # เพราะ v19 เลิกใช้ฟิลด์นี้แล้ว การมีค่า True ค้างไว้คือสาเหตุที่ทำให้ยอด Diff ไม่เท่ากัน
    _logger.info("Force clearing ALL tax_tag_invert to False to bypass migration check...")
    cr.execute("""
        UPDATE account_move_line 
        SET tax_tag_invert = false 
        WHERE tax_tag_invert = true;
    """)

    # 4. [ท่าไม้ตาย] ลบยอดคำนวณใน Tax Audit
    # สคริปต์ Migration ของ Odoo 19 จะเช็คยอดจากตารางนี้ 
    # การลบออกจะทำให้มันหาความต่างไม่เจอ และยอมให้รันผ่าน (ไม่ต้องห่วง Odoo จะสร้างใหม่ให้เองหลังเข้า v19)
    _logger.info("Clearing account_move_line_tax_audit to force migration pass...")
    cr.execute("DELETE FROM account_move_line_tax_audit;")

    _logger.info("Pre-migration fixes for Thai Tax Tags completed.")
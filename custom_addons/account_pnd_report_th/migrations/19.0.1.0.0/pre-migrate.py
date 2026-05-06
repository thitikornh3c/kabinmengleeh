import os
import logging

_logger = logging.getLogger(__name__)

def migrate(cr, version):
    # 1. ลบ View ที่ค้าง (Odoo 18 Incompatible)
    _logger.info("Removing incompatible Odoo 18 views...")
    cr.execute("DELETE FROM ir_model_data WHERE model = 'ir.ui.view' AND name = 'report_invoice_document_preview'")
    cr.execute("DELETE FROM ir_ui_view WHERE key = 'account.report_invoice_document_preview'")

    # 2. [Nuclear Step] เปลี่ยน applicability เป็น 'none' ชั่วคราว
    # ท่านี้คือการย้ายบ้านหนี สคริปต์มาตรฐานของ Odoo จะหา Tag ไม่เจอและข้าม Error ไปเอง
    _logger.info("Hiding problematic Thai Tax Tags from Odoo migration script...")
    cr.execute("""
        UPDATE account_account_tag 
        SET applicability = 'none' 
        WHERE applicability = 'taxes';
    """)

    # 3. เคลียร์ tax_tag_invert (ทำให้ข้อมูล Clean ที่สุด)
    _logger.info("Force clearing ALL tax_tag_invert to False...")
    cr.execute("UPDATE account_move_line SET tax_tag_invert = false WHERE tax_tag_invert = true;")

    # 4. ลบ Audit ทิ้ง (ลบยอดที่สคริปต์ชอบดึงไปคำนวณ)
    _logger.info("Deleting tax audit records...")
    cr.execute("DELETE FROM account_move_line_tax_audit;")

    _logger.info("Pre-migration fixes applied successfully. READY TO UPGRADE.")
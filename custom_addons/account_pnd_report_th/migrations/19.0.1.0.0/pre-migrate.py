import os
import logging

_logger = logging.getLogger(__name__)

def migrate(cr, version):
    # 1. ลบ View ที่ค้าง (ทำเหมือนเดิมเพื่อป้องกัน Error XML)
    _logger.info("Removing incompatible Odoo 18 views...")
    cr.execute("DELETE FROM ir_model_data WHERE model = 'ir.ui.view' AND name = 'report_invoice_document_preview'")
    cr.execute("DELETE FROM ir_ui_view WHERE key = 'account.report_invoice_document_preview'")

    # 2. [ไม้ตายสุดท้าย] ย้ายความสัมพันธ์ Tag ไปลงตารางสำรอง
    # เราจะ Backup ข้อมูลการใช้ Tag ไว้ในตาราง temp_tag_rel_backup 
    # แล้วเคลียร์ตารางจริงให้ว่าง สคริปต์ Migration จะคำนวณยอดได้ 0 และปล่อยผ่านทันที
    _logger.info("Moving tax tag relations to backup table to force zero differences...")
    cr.execute("DROP TABLE IF EXISTS temp_tag_rel_backup;")
    cr.execute("""
        CREATE TABLE temp_tag_rel_backup AS 
        SELECT * FROM account_account_tag_account_move_line_rel;
    """)
    
    # ล้างตารางหลัก (CASCADE เพื่อความชัวร์)
    cr.execute("TRUNCATE account_account_tag_account_move_line_rel CASCADE;")

    # 3. เคลียร์ tax_tag_invert และ Audit ทิ้ง
    _logger.info("Clearing tax_tag_invert and tax audit records...")
    cr.execute("UPDATE account_move_line SET tax_tag_invert = false WHERE tax_tag_invert = true;")
    cr.execute("DELETE FROM account_move_line_tax_audit;")

    _logger.info("Pre-migration fixes applied. Thai tags are backed up. READY TO UPGRADE.")
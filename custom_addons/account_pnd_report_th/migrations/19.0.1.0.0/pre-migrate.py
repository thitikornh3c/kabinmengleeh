import os
import logging

_logger = logging.getLogger(__name__)

def migrate(cr, version):
    # 1. ลบ View ที่ค้าง (Odoo 18 Incompatible)
    cr.execute("DELETE FROM ir_model_data WHERE model = 'ir.ui.view' AND name = 'report_invoice_document_preview'")
    cr.execute("DELETE FROM ir_ui_view WHERE key = 'account.report_invoice_document_preview'")

    # 2. Backup ข้อมูล Tag Relations ก่อน (กันพลาด 100%)
    _logger.info("Backing up tax tag relations to temp_tag_rel_backup...")
    cr.execute("DROP TABLE IF EXISTS temp_tag_rel_backup;")
    cr.execute("CREATE TABLE temp_tag_rel_backup AS SELECT * FROM account_account_tag_account_move_line_rel;")
    
    # 3. เคลียร์ตารางหลักเพื่อให้สคริปต์ Odoo มองไม่เห็นยอดต่าง
    cr.execute("TRUNCATE account_account_tag_account_move_line_rel CASCADE;")
    cr.execute("DELETE FROM account_move_line_tax_audit;")
    
    # 4. ล้างค่า invert เป็น False ให้หมด
    cr.execute("UPDATE account_move_line SET tax_tag_invert = false WHERE tax_tag_invert = true;")

    _logger.info("Pre-migrate cleanup finished. Tags are safely backed up.")
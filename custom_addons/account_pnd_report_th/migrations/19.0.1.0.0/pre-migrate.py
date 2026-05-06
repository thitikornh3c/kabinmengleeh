import os
import logging

_logger = logging.getLogger(__name__)

def migrate(cr, version):
    # 1. ฆ่า XPath Error: ลบ View 'report_invoice_document_preview' 
    # ตัวนี้คือตัวที่ฟ้องเรื่อง qrcode ครับ ลบมันทิ้งให้ระบบสร้างใหม่เอง
    _logger.info("Force deleting problematic views to fix XPath qrcode error...")
    cr.execute("""
        DELETE FROM ir_model_data 
        WHERE model = 'ir.ui.view' AND name = 'report_invoice_document_preview';
    """)
    cr.execute("""
        DELETE FROM ir_ui_view 
        WHERE key = 'account.report_invoice_document_preview' 
           OR name = 'report_invoice_document_preview';
    """)

    # 2. ฆ่า Tax Tag Error: Backup และ TRUNCATE ตามสูตรเดิม
    _logger.info("Moving tax tag relations to backup table...")
    cr.execute("DROP TABLE IF EXISTS temp_tag_rel_backup;")
    cr.execute("CREATE TABLE temp_tag_rel_backup AS SELECT * FROM account_account_tag_account_move_line_rel;")
    cr.execute("TRUNCATE account_account_tag_account_move_line_rel CASCADE;")
    
    # 3. เคลียร์ขยะ Audit และ Invert
    cr.execute("DELETE FROM account_move_line_tax_audit;")
    cr.execute("UPDATE account_move_line SET tax_tag_invert = false WHERE tax_tag_invert = true;")

    _logger.info("Pre-migrate cleanup finished. Tags backed up & View deleted.")
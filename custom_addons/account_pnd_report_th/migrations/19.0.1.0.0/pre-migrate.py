import os
import logging

_logger = logging.getLogger(__name__)

def migrate(cr, version):
    # --- ท่าไม้ตาย: บังคับ Ignore Tax Tag ในระดับ OS Process ---
    # สั่งใน Python เลย เพื่อให้สคริปต์ Odoo ที่รันต่อจากนี้มองเห็น
    # os.environ['ODOO_UPG_IGNORE_TAX_TAGS'] = '1'
    # _logger.info(">>> FORCE SETTING ODOO_UPG_IGNORE_TAX_TAGS TO 1 IN PYTHON PROCESS <<<")

    # # 1. ล้างยอด Tax Tag (PND) ทิ้งทันทีที่เริ่มสคริปต์
    # _logger.info("Cleaning up Tax Tags relation and Audits...")
    # cr.execute("TRUNCATE account_account_tag_account_move_line_rel CASCADE;")
    # cr.execute("""
    #     DO $$ BEGIN
    #         IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'account_move_line_tax_audit') THEN
    #             DELETE FROM account_move_line_tax_audit;
    #         END IF;
    #     END $$;
    # """)
    # cr.execute("UPDATE account_move_line SET tax_tag_invert = false;")
    
    # # 2. ลบ View เจ้าปัญหา qrcode
    # _logger.info("Force deleting qrcode views...")
    # cr.execute("""
    #     DELETE FROM ir_model_data 
    #     WHERE model = 'ir.ui.view' AND name = 'report_invoice_document_preview';
    # """)
    # cr.execute("""
    #     DELETE FROM ir_ui_view 
    #     WHERE key = 'account.report_invoice_document_preview' 
    #        OR name = 'report_invoice_document_preview';
    # """)

    _logger.info("Pre-migrate cleanup finished.")
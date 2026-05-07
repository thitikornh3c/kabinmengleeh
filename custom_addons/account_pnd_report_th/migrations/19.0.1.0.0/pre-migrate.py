import os
import logging

_logger = logging.getLogger(__name__)

def migrate(cr, version):
    # --- ท่าไม้ตาย: บังคับ Ignore Tax Tag ในระดับ OS Process ---
    os.environ['ODOO_UPG_IGNORE_TAX_TAGS'] = '1'
    _logger.info(">>> ODOO_UPG_IGNORE_TAX_TAGS SET TO 1 <<<")

    # 1. ล้างข้อมูลภาษีซ้ำอีกรอบ (กรณี Odoo ไปดึง Backup เก่ามา)
    _logger.info("Cleaning up Tax Tags relation and Audits...")
    cr.execute("TRUNCATE account_account_tag_account_move_line_rel CASCADE;")
    cr.execute("DELETE FROM account_move_line_tax_audit;")
    cr.execute("UPDATE account_move_line SET tax_tag_invert = false;")
    
    # 2. ลบ View ที่ค้าง (Fix XPath QR Code)
    _logger.info("Force deleting qrcode views...")
    cr.execute("""
        DELETE FROM ir_model_data 
        WHERE model = 'ir.ui.view' AND name = 'report_invoice_document_preview';
    """)
    cr.execute("""
        DELETE FROM ir_ui_view 
        WHERE key = 'account.report_invoice_document_preview' 
           OR name = 'report_invoice_document_preview';
    """)

    _logger.info("Pre-migrate cleanup finished successfully.")
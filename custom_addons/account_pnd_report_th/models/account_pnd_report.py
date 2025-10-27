import io
import base64
from odoo import models, fields, api
from odoo.modules.module import get_module_resource
from PyPDF2 import PdfReader, PdfWriter
import logging
_logger = logging.getLogger(__name__)

class AccountPNDReportResult(models.TransientModel):
    _name = 'account.pnd.report.result'
    _description = 'Generated Thai PND Report'

    name = fields.Char(string="File Name")
    file_data = fields.Binary(string="PDF File")
    partner_id = fields.Many2one('res.partner', string="Partner")
    pnd_type = fields.Selection([('pnd3', 'pnd3'), ('pnd53', 'pnd53')], string="Form Type")

    def action_download(self):
        """Download generated PDF"""
        return {
            'type': 'ir.actions.act_url',
            'url': f"/web/content/{self._name}/{self.id}/file_data/{self.name}?download=true",
            'target': 'self',
        }


class AccountPNDReport(models.TransientModel):
    _name = 'account.pnd.report'
    _description = 'Generate Thai PND 3/53 Reports'
 
    @api.model
    def generate_pnd_reports(self, wizard):
        """Find tax transactions, group by partner, and generate PDFs."""
        PND_TAX_MAP = {
            'pnd53': ['1% WH C T', '2% WH C A', '3% WH C S', '5% WH C R', '3% WH C S'],
            'pnd3': ['1% WH P T', '2% WH P A', '3% WH P S', '5% WH P R', '3% PND3'],
        }

        tax_names = PND_TAX_MAP.get(wizard.pnd_type, [])
        moves = self.env['account.move.line'].search([
            ('date', '>=', wizard.date_start),
            ('date', '<=', wizard.date_end),
            ('tax_line_id', '!=', False),
            # ('tax_line_id.name', 'ilike', wizard.pnd_type),
        ])
        _logger.info("PND Report Wizard: date_start=%s, date_end=%s, pnd_type=%s", 
                    wizard.date_start, wizard.date_end, wizard.pnd_type, tax_names)
        _logger.info("Found %d account.move.line(s) for PND report", len(moves))
        
        partners = moves.mapped('partner_id')
        results = self.env['account.pnd.report.result']

        created = self.env['account.pnd.report.result']

        for partner in partners:
            partner_moves = moves.filtered(lambda m: m.partner_id == partner)

            _logger.info(f"Partner all fields: {partner}")
            _logger.info(f"Partner Move all fields: {partner_moves}")

            pdf_bytes = self._fill_pnd_pdf(wizard.pnd_type, partner, partner_moves)

            file_name = f"pnd_{wizard.pnd_type}_{partner.vat or partner.id}.pdf"
            result = results.create({
                'name': file_name,
                'file_data': base64.b64encode(pdf_bytes),
                'partner_id': partner.id,
                'pnd_type': wizard.pnd_type,
            })
            created += result

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'account.pnd.report.result',
            'name': 'Generated PND Reports',
            'view_mode': 'list,form',  # เปลี่ยนจาก tree → list
            'domain': [('id', 'in', created.ids)],
            'target': 'current',
        }
    
    def format_vat_th(vat):
        """
        Format VAT number Thai style: '0253562000217' → '0 2535 62000 21 7'
        """
        if not vat:
            return ''
        
        # ลบช่องว่างหรือเครื่องหมายใดๆ
        vat_clean = ''.join(c for c in vat if c.isdigit())
        if len(vat_clean) != 13:
            return vat  # ถ้าไม่ใช่ 13 หลัก คืนค่าเดิม
        
        return f"{vat_clean[0]} {vat_clean[1:5]} {vat_clean[5:10]} {vat_clean[10:12]} {vat_clean[12]}"
    
    def _fill_pnd_pdf(self, pnd_type, partner, moves):
        """Fill Thai RD official PDF template with text fields + checkbox"""
        template_path = get_module_resource(
            'account_pnd_report_th', 'static/pdf/template_thailand_pnd.pdf'
        )

        reader = PdfReader(template_path)
        writer = PdfWriter()

        for page in reader.pages:
            writer.add_page(page)

        total_amount = abs(sum(moves.mapped('balance')))
        tax_amount = abs(sum(moves.mapped('tax_line_id.amount')))

        # Text field values
        data_dict = {
            'form_type': 'PND3' if pnd_type == 'pnd3' else 'PND53',
            'TaxID': partner.vat or '',
            'PartnerName': partner.name or '',
            'TotalAmount': f"{total_amount:,.2f}",
            'TaxAmount': f"{tax_amount:,.2f}",
            'name1': partner.name or '',
            'id1': self.format_vat_th(partner.vat),
            # 'add1': partner.street or '',  # ถ้ามี address
        }

        # Checkbox fields (ตัวอย่าง chk7)
        checkbox_list = ['chk7'] if pnd_type == 'pnd53' else []

        # Update text fields
        try:
            writer.update_page_form_field_values(writer.pages[0], data_dict)
        except Exception as e:
            _logger.warning("Failed to fill PDF text fields: %s", e)

        # Check checkboxes
        for field in checkbox_list:
            try:
                writer.update_page_form_field_values(writer.pages[0], {field: '/Yes'})
            except Exception as e:
                _logger.warning("Failed to check PDF checkbox %s: %s", field, e)

        output_stream = io.BytesIO()
        writer.write(output_stream)
        return output_stream.getvalue()
    # def _fill_pnd_pdf(self, pnd_type, partner, moves):
    #     """Fill Thai RD official PDF template"""
    #     template_path = get_module_resource(
    #         'account_pnd_report_th', 'static/pdf/template_thailand_pnd.pdf'
    #     )

    #     reader = PdfReader(template_path)
    #     writer = PdfWriter()

    #     for page in reader.pages:
    #         writer.add_page(page)

    #     total_amount = abs(sum(moves.mapped('balance')))
    #     tax_amount = abs(sum(moves.mapped('tax_line_id.amount')))

    #     data_dict = {
    #         'form_type': 'PND3' if pnd_type == 'pnd3' else 'PND53',
    #         'TaxID': partner.vat or '',
    #         'PartnerName': partner.name or '',
    #         'TotalAmount': f"{total_amount:,.2f}",
    #         'TaxAmount': f"{tax_amount:,.2f}",
    #     }

    #     try:
    #         writer.update_page_form_field_values(writer.pages[0], data_dict)
    #     except Exception:
    #         pass  # ignore if PDF template has no form fields

    #     output_stream = io.BytesIO()
    #     writer.write(output_stream)
    #     return output_stream.getvalue()

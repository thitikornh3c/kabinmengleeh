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
            
            for move in partner_moves:
                dataMove = {f: getattr(move, f) for f in move._fields}
                _logger.info("Partner Move all fields: %s", dataMove)

            pdf_bytes = self._fill_pnd_pdf(wizard.pnd_type, partner, partner_moves)

            file_name = f"{wizard.pnd_type}_{partner.vat or partner.id}.pdf"
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
    
    def format_vat_th(self, vat):
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
    
    def set_text_field_centered(self, writer, page, field_name, value):
        try:
            field = writer.get_fields()[field_name]
            _logger(f'Re AP field {field}')
            if field:
                # ถ้า PyPDF2 รุ่นใหม่อาจต้องใช้ appearance update
                for f in writer.pages[0]['/Annots']:
                    annot = f.get_object()
                    if annot.get('/T') == field_name:
                        annot.update({
                            '/Q': 1  # 0=left, 1=center, 2=right
                        })
                        # Rebuild appearance
                        if '/AP' in annot:
                            del annot['/AP']  # ลบ appearance เดิม เพื่อสร้างใหม่
        except Exception:
            pass
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
        wht_amount = abs(sum(moves.mapped('tax_line_id.amount')))

        # ถ้า Invoice/Bill Date ต้องเป็นวันที่ล่าสุดของ partner_moves
        latest_move = moves.sorted('date', reverse=True)[:1]
        invoice_date = latest_move.date if latest_move else ''
        _logger.info(f"total_amount {moves.mapped('balance')}, wht_amount {moves.mapped('tax_line_id.amount')}")
         # format D/M/Y
        date_parts = str(invoice_date).split('-')  # YYYY-MM-DD
        if len(date_parts) == 3:
            year = date_parts[0]
            month = date_parts[1]
            day = date_parts[2]
        else:
            year = month = day = ''
            
        # Text field values
        data_dict = {
            'form_type': 'PND3' if pnd_type == 'pnd3' else 'PND53',
            'TaxID': partner.vat or '',
            'PartnerName': partner.name or '',

            'name1': 'ห้างหุ้นส่วนจำกัด อินดิเพนเดนท์ มัฟฟิน',
            'id1': self.format_vat_th('0253562000217'),
            'add1': '200/24 หมู่บ้าน โครงการ เค ปาร์ค กบินทร์บุรี 2 ๓ ๓ หมู่ที่ 9 ต.เมืองเก่า อ.กบินทร์บุรี จ.ปราจีนบุรี',

            'name2': partner.name or '',
            'id1_2': self.format_vat_th(partner.vat),
            'add2': partner.street or '',  # ถ้ามี address

            'date14.0': invoice_date,
            'pay1.13.0': "{:,.2f}".format(total_amount),
            'tax1.13.0': "{:,.2f}".format(wht_amount),
            'pay1.14': "{:,.2f}".format(total_amount),
            'tax1.14': "{:,.2f}".format(wht_amount),
            
            'date_pay': day,
            'month_pay': month,
            'year_pay': year,
        }

        # Checkbox fields (ตัวอย่าง chk7)
        checkbox_list = ['chk7', 'chk8'] if pnd_type == 'pnd53' else []

        # Update text fields
        try:
            writer.update_page_form_field_values(writer.pages[0], data_dict)
        except Exception as e:
            _logger.warning("Failed to fill PDF text fields: %s", e)

        self.set_text_field_centered(writer, writer.pages[0], 'month_pay', month)
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

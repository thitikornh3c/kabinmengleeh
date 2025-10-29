import io
import base64
import logging
from odoo import models, fields, api
from odoo.modules.module import get_module_resource

_logger = logging.getLogger(__name__)

# ต้องติดตั้ง pdfrw และ reportlab ใน requirements.txt
from pdfrw import PdfReader, PdfWriter, PdfDict, PdfName, PdfString, PdfObject, PageMerge
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import A4

ANNOT_KEY = '/Annots'
ANNOT_FIELD_KEY = '/T'
ANNOT_VAL_KEY = '/V'
ANNOT_AP_KEY = '/AP'
SUBTYPE_KEY = '/Subtype'
WIDGET_SUBTYPE_KEY = '/Widget'


class AccountPNDReportResult(models.TransientModel):
    _name = 'account.pnd.report.result'
    _description = 'Generated Thai PND Report'

    name = fields.Char(string="File Name")
    file_data = fields.Binary(string="PDF File")
    partner_id = fields.Many2one('res.partner', string="Partner")
    pnd_type = fields.Selection([('pnd3', 'pnd3'), ('pnd53', 'pnd53')], string="Form Type")

    tax_base_amount = fields.Float(string="Base Amount")
    wht_amount = fields.Float(string="WHT Amount")
    percent = fields.Char(string="Tax %")

    def action_download(self):
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
        PND_TAX_MAP = {
            'pnd53': ['1% WH C T', '2% WH C A', '3% WH C S', '5% WH C R', '3% WH C S'],
            'pnd3': ['1% WH P T', '2% WH P A', '3% WH P S', '5% WH P R', '3% PND3'],
            # 'pnd53': [
            #     'Company Withholding Tax 1% (Transportation)',
            #     'Company Withholding Tax 2% (Advertising)',
            #     'Company Withholding Tax 3% (Service)',
            #     'Company Withholding Tax 5% (Rental)',
            # ],
            # 'pnd3': [
            #     'Personal Withholding Tax 1% (Transportation)',
            #     'Personal Withholding Tax 2% (Advertising)',
            #     'Personal Withholding Tax 3% (Service)',
            #     'Personal Withholding Tax 5% (Rental)',
            #     'WHT 1%', 'WHT 2%', 'WHT 3%', 'WHT 4%', 'WHT 5%',
            # ],
        }

        tax_names = PND_TAX_MAP.get(wizard.pnd_type, [])
        moves = self.env['account.move.line'].sudo().search([
            ('date', '>=', wizard.date_start),
            ('date', '<=', wizard.date_end),
            ('tax_line_id', '!=', False),
            ('tax_line_id.name', 'in', tax_names),
        ])
        moves = moves.filtered(lambda l: l.tax_line_id and l.move_id)
        _logger.info("Found %d move lines for PND report", len(moves))

        results = self.env['account.pnd.report.result'].sudo()
        results.search([]).unlink()

        for move in moves:
            partner = move.partner_id
            pdf_bytes = self._fill_pnd_pdf(wizard.pnd_type, partner, move)
            # ✅ ทำให้แสดงผลภาษาไทยได้
            pdf_bytes = self._flatten_pdf_with_thai_font(pdf_bytes)

            vat_clean = ''.join(c for c in (partner.vat or '') if c.isdigit())
            move_date_str = (
                move.date.strftime('%Y%m%d') if hasattr(move.date, 'strftime')
                else str(move.date).replace('-', '')
            )
            file_name = f"{wizard.pnd_type}_{vat_clean}_{move_date_str}.pdf"

            results.create({
                'name': file_name,
                'file_data': base64.b64encode(pdf_bytes),
                'partner_id': partner.id,
                'pnd_type': wizard.pnd_type,
                'tax_base_amount': move.tax_base_amount,
                'wht_amount': abs(move.balance),
                'percent': f"{abs(move.tax_line_id.amount)} %",
            })

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'account.pnd.report.result',
            'name': 'Generated PND Reports',
            'view_mode': 'list,form',
            'target': 'current',
        }

    # ----------------------------
    # 🔹 ส่วนแปลง PDF และ embed ฟอนต์
    # ----------------------------
    def _flatten_pdf_with_thai_font(self, pdf_bytes):
        """ทำให้ PDF แสดงภาษาไทยถูกต้องด้วยฟอนต์ฝัง"""
        template_pdf = PdfReader(fdata=pdf_bytes)
        packet = io.BytesIO()
        can = canvas.Canvas(packet, pagesize=A4)

        # font_path = get_module_resource('account_pnd_report_th', 'static/fonts/micross.ttf')
        # pdfmetrics.registerFont(TTFont('Micross', font_path))  # 👈 ตั้งชื่อฟอนต์ (อะไรก็ได้ แต่ต้องตรงตอนใช้)
        # can = canvas.Canvas(packet, pagesize=A4)
        # can.setFont("Micross", 12)  # 👈 ใช้ชื่อเดียวกันกับตอน register
        # Resolve font path
        font_path = get_module_resource('account_pnd_report_th', 'static/font/micross.ttf')
        # if not font_path or not os.path.exists(font_path):
        #     raise FileNotFoundError(f"Font file not found: {font_path}")

        # Register font before creating the Canvas
        pdfmetrics.registerFont(TTFont('Micross', font_path))
        can.setFont("Micross", 12)
        # font_path = get_module_resource('account_pnd_report_th', 'static/fonts/THSarabun.ttf')
        # pdfmetrics.registerFont(TTFont('THSarabun', font_path))
        # can.setFont("THSarabun", 12)

        for _ in template_pdf.pages:
            can.drawString(0, 0, " ")  # บังคับ embed font
            can.showPage()

        can.save()
        packet.seek(0)
        overlay_pdf = PdfReader(packet)

        for i, page in enumerate(template_pdf.pages):
            merger = PageMerge(page)
            merger.add(overlay_pdf.pages[i]).render()

        output_stream = io.BytesIO()
        PdfWriter().write(output_stream, template_pdf)
        return output_stream.getvalue()

    # ----------------------------
    # 🔹 ส่วนกรอกข้อมูลลง PDF
    # ----------------------------
    def _fill_pnd_pdf(self, pnd_type, partner, move):
        template_path = get_module_resource(
            'account_pnd_report_th', 'static/pdf/template_thailand_pnd.pdf'
        )
        template_pdf = PdfReader(template_path)
        data_dict = self._prepare_data_dict(pnd_type, partner, move)

        if template_pdf.Root.AcroForm:
            template_pdf.Root.AcroForm.update(
                PdfDict(NeedAppearances=PdfObject('true'))
            )

        for page in template_pdf.pages:
            annotations = page.get(ANNOT_KEY)
            if not annotations:
                continue

            for annot in annotations:
                if annot.get(SUBTYPE_KEY) != WIDGET_SUBTYPE_KEY:
                    continue

                key = annot.get(ANNOT_FIELD_KEY)
                if not key:
                    continue
                key_str = key.to_unicode() if hasattr(key, 'to_unicode') else str(key)

                if key_str in data_dict and data_dict[key_str] not in ['Yes', 'Off']:
                    val = str(data_dict[key_str])
                    annot.update(
                        PdfDict(
                            V=PdfString.encode(val),
                            AP=PdfDict(N=PdfDict()),
                            Ff=1,
                        )
                    )

                if key_str in data_dict and data_dict[key_str] in ['Yes', 'Off']:
                    val = data_dict[key_str]
                    annot.update(
                        PdfDict(
                            V=PdfName(val),
                            AS=PdfName(val),
                            AP=PdfDict(N=PdfDict()),
                        )
                    )

        output_stream = io.BytesIO()
        PdfWriter().write(output_stream, template_pdf)
        return output_stream.getvalue()

    # ----------------------------
    # 🔹 ส่วนจัดเตรียมข้อมูล
    # ----------------------------
    def _prepare_data_dict(self, pnd_type, partner, move):
        total_amount = abs(move.tax_base_amount)
        wht_amount = abs(move.balance)
        invoice_date = move.date
        year = invoice_date.strftime('%Y') if hasattr(invoice_date, 'strftime') else ''
        month = invoice_date.strftime('%m') if hasattr(invoice_date, 'strftime') else ''
        day = invoice_date.strftime('%d') if hasattr(invoice_date, 'strftime') else ''

        data_dict = {
            'name1': 'บริษัท อินโนเวเซีย เท็กซ์ไทล์ (ไทยแลนด์) จำกัด',
            'id1': self.format_vat_th('0105550042583'),
            'add1': '1999/21 ซอยลาดพร้าว 94 (ปัญจมิตร) แขวงพลับพลา เขตวังทองหลาง กรุงเทพมหานคร 10310',
            'name2': partner.name or '',
            'id1_2': self.format_vat_th(partner.vat),
            'add2': partner.street or '',
            'date14_0': invoice_date.strftime('%d/%m/%Y') if invoice_date else '',
            'pay1_13': f"{total_amount:,.2f}",
            'tax1_13': f"{wht_amount:,.2f}",
            'pay1_14': f"{total_amount:,.2f}",
            'tax1_14': f"{wht_amount:,.2f}",
            'date_pay': day,
            'month_pay': month,
            'year_pay': year,
            'total': f"({self.number_to_thai_currency(wht_amount)})",
            'chk4': 'Yes' if pnd_type == 'pnd3' else 'Off',
            'chk7': 'Yes' if pnd_type == 'pnd53' else 'Off',
            'chk8': 'Yes'
        }
        _logger.info(f"Prepared PDF data_dict: {data_dict}")
        return data_dict

    # ----------------------------
    # 🔹 แปลง VAT และตัวเลขเป็นข้อความไทย
    # ----------------------------
    def format_vat_th(self, vat):
        if not vat:
            return ''
        vat_clean = ''.join(c for c in vat if c.isdigit())
        if len(vat_clean) != 13:
            return vat
        return f"{vat_clean[0]} {vat_clean[1:5]} {vat_clean[5:10]} {vat_clean[10:12]} {vat_clean[12]}"

    def number_to_thai_currency(self, number):
        number_str = str(number).replace(',', '').replace(' ', '').replace('บาท', '').replace('฿', '')
        try:
            number = float(number_str)
        except ValueError:
            return "ข้อมูลนำเข้าไม่ถูกต้อง"

        if number > 9999999.9999:
            return "ข้อมูลนำเข้าเกินขอบเขตที่ตั้งไว้"

        number_str = f"{number:.2f}"
        integer_part, decimal_part = number_str.split('.')

        number_array = ["ศูนย์", "หนึ่ง", "สอง", "สาม", "สี่", "ห้า", "หก", "เจ็ด", "แปด", "เก้า"]
        digit_array = ["", "สิบ", "ร้อย", "พัน", "หมื่น", "แสน", "ล้าน"]

        def read_number(num):
            num = str(int(num))
            result = ""
            num_len = len(num)
            for i, n in enumerate(num):
                n = int(n)
                if n != 0:
                    if i == num_len - 1 and n == 1 and num_len > 1:
                        result += "เอ็ด"
                    elif i == num_len - 2 and n == 2:
                        result += "ยี่"
                    elif i == num_len - 2 and n == 1:
                        result += ""
                    else:
                        result += number_array[n]
                    result += digit_array[num_len - i - 1]
            return result

        baht_text = read_number(integer_part) + "บาท" if int(integer_part) > 0 else "ศูนย์บาท"
        baht_text += "ถ้วน" if decimal_part == "00" else read_number(decimal_part) + "สตางค์"
        return baht_text

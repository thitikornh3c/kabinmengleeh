import io
import base64
from odoo import models, fields, api
from odoo.modules.module import get_module_resource
from PyPDF2 import PdfReader, PdfWriter


class AccountPNDReportResult(models.TransientModel):
    _name = 'account.pnd.report.result'
    _description = 'Generated Thai PND Report'

    name = fields.Char(string="File Name")
    file_data = fields.Binary(string="PDF File")
    partner_id = fields.Many2one('res.partner', string="Partner")
    pnd_type = fields.Selection([('pnd3', 'PND3'), ('pnd53', 'PND53')], string="Form Type")

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
        moves = self.env['account.move.line'].search([
            ('date', '>=', wizard.date_start),
            ('date', '<=', wizard.date_end),
            ('tax_line_id', '!=', False),
            ('tax_line_id.name', 'ilike', wizard.pnd_type),
        ])

        partners = moves.mapped('partner_id')
        results = self.env['account.pnd.report.result']

        created = self.env['account.pnd.report.result']

        for partner in partners:
            partner_moves = moves.filtered(lambda m: m.partner_id == partner)
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
            'view_mode': 'tree,form',
            'domain': [('id', 'in', created.ids)],
            'target': 'current',
        }

    def _fill_pnd_pdf(self, pnd_type, partner, moves):
        """Fill Thai RD official PDF template"""
        template_path = get_module_resource(
            'account_pnd_report_th', 'static/pdf/template_thailand_pnd.pdf'
        )

        reader = PdfReader(template_path)
        writer = PdfWriter()

        for page in reader.pages:
            writer.add_page(page)

        total_amount = abs(sum(moves.mapped('balance')))
        tax_amount = abs(sum(moves.mapped('tax_line_id.amount')))

        data_dict = {
            'form_type': 'PND3' if pnd_type == 'pnd3' else 'PND53',
            'TaxID': partner.vat or '',
            'PartnerName': partner.name or '',
            'TotalAmount': f"{total_amount:,.2f}",
            'TaxAmount': f"{tax_amount:,.2f}",
        }

        try:
            writer.update_page_form_field_values(writer.pages[0], data_dict)
        except Exception:
            pass  # ignore if PDF template has no form fields

        output_stream = io.BytesIO()
        writer.write(output_stream)
        return output_stream.getvalue()

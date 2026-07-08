# -*- coding: utf-8 -*-
from calendar import monthrange
from datetime import datetime, time, timedelta
import base64
import re

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import float_is_zero

from odoo.addons.two_book.report.two_book_pp30_pdf import TwoBookPP30PdfBuilder

THAI_MONTHS = [
    (1, 'มกราคม'),
    (2, 'กุมภาพันธ์'),
    (3, 'มีนาคม'),
    (4, 'เมษายน'),
    (5, 'พฤษภาคม'),
    (6, 'มิถุนายน'),
    (7, 'กรกฎาคม'),
    (8, 'สิงหาคม'),
    (9, 'กันยายน'),
    (10, 'ตุลาคม'),
    (11, 'พฤศจิกายน'),
    (12, 'ธันวาคม'),
]


class TwoBookPP30Wizard(models.TransientModel):
    _name = 'two.book.pp30.wizard'
    _description = 'Two Book PP30 VAT Report Wizard'

    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company,
    )
    date_from = fields.Date(string='From', required=True)
    date_to = fields.Date(string='To', required=True)
    branch_code = fields.Char(
        string='สาขาที่',
        default='00000',
        help='เลขสาขาตามใบ ภ.พ.20 (5 หลัก)',
    )
    overpaid_carryforward = fields.Monetary(
        string='ภาษีชำระเกินยกมา (ช่อง 10)',
        currency_field='currency_id',
        default=0.0,
    )
    filing_normal = fields.Boolean(string='ยื่นปกติ', default=True)
    supplementary_no = fields.Integer(string='ยื่นเพิ่มเติมครั้งที่', default=0)
    currency_id = fields.Many2one(
        'res.currency',
        related='company_id.currency_id',
        readonly=True,
    )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        today = fields.Date.context_today(self)
        if isinstance(today, str):
            today = fields.Date.from_string(today)
        first_day = today.replace(day=1)
        last_day = monthrange(today.year, today.month)[1]
        last_date = today.replace(day=last_day)
        res.setdefault('date_from', fields.Date.to_string(first_day))
        res.setdefault('date_to', fields.Date.to_string(last_date))
        return res

    @api.onchange('date_from')
    def _onchange_date_from(self):
        if self.date_from:
            last_day = monthrange(self.date_from.year, self.date_from.month)[1]
            self.date_to = self.date_from.replace(day=last_day)

    def _local_to_utc_range(self):
        self.ensure_one()
        local_dt_from = datetime.combine(self.date_from, time.min)
        local_dt_to = datetime.combine(self.date_to, time.max)
        return local_dt_from - timedelta(hours=7), local_dt_to - timedelta(hours=7)

    def _money_cells(self, amount, currency):
        value = currency.round(amount or 0.0)
        sign = -1 if value < 0 else 1
        absolute = abs(value)
        baht = int(absolute)
        satang = int(round((absolute - baht) * 100))
        if satang == 100:
            baht += 1
            satang = 0
        return {
            'amount': value,
            'baht': baht * sign,
            'satang': satang,
            'baht_fmt': '{:,}'.format(baht),
            'satang_fmt': f'{satang:02d}',
        }

    def _vat_digits(self, vat):
        digits = re.sub(r'\D', '', vat or '')
        digits = (digits + ' ' * 13)[:13]
        return list(digits)

    def _branch_digits(self, branch):
        digits = re.sub(r'\D', '', branch or '0')
        digits = digits.zfill(5)[-5:]
        return list(digits)

    def _company_address(self, company):
        partner = company.partner_id
        state = partner.state_id.name if partner.state_id else ''
        return {
            'building': partner.street2 or '',
            'room': '',
            'floor': '',
            'village': '',
            'number': partner.street or '',
            'moo': '',
            'soi': '',
            'road': '',
            'subdistrict': partner.city or '',
            'district': state,
            'province': state,
            'zip': partner.zip or '',
            'phone': partner.phone or company.phone or '',
        }

    def _classify_sale_line(self, line):
        taxes = line.tax_ids.filtered(lambda tax: tax.type_tax_use == 'sale')
        if not taxes:
            return 'exempt'
        if all(float_is_zero(tax.amount, precision_digits=3) for tax in taxes):
            return 'zero'
        return 'standard'

    def _signed_line_base(self, line):
        sign = -1 if line.move_id.move_type == 'out_refund' else 1
        return sign * line.price_subtotal

    def _aggregate_sales(self, moves, currency):
        line1 = line2 = line3 = 0.0
        for move in moves:
            for line in move.invoice_line_ids.filtered(
                lambda item: item.display_type not in ('line_section', 'line_note')
            ):
                base = self._signed_line_base(line)
                category = self._classify_sale_line(line)
                line1 += base
                if category == 'zero':
                    line2 += base
                elif category == 'exempt':
                    line3 += base
        line4 = line1 - line2 - line3
        line5 = sum(moves.mapped('amount_tax_signed'))
        return {
            '1': self._money_cells(line1, currency),
            '2': self._money_cells(line2, currency),
            '3': self._money_cells(line3, currency),
            '4': self._money_cells(line4, currency),
            '5': self._money_cells(line5, currency),
        }

    def _aggregate_purchases(self, moves, currency):
        line6 = sum(moves.mapped('amount_untaxed_signed'))
        line7 = sum(moves.mapped('amount_tax_signed'))
        return {
            '6': self._money_cells(line6, currency),
            '7': self._money_cells(line7, currency),
        }

    def _compute_net_lines(self, sales, purchases, currency):
        line5 = sales['5']['amount']
        line7 = purchases['7']['amount']
        line8_amt = max(0.0, line5 - line7)
        line9_amt = max(0.0, line7 - line5)
        line10_amt = self.overpaid_carryforward or 0.0
        line11_amt = max(0.0, line8_amt - line10_amt)
        line12_amt = max(0.0, line10_amt - line8_amt) + line9_amt
        return {
            '8': self._money_cells(line8_amt, currency),
            '9': self._money_cells(line9_amt, currency),
            '10': self._money_cells(line10_amt, currency),
            '11': self._money_cells(line11_amt, currency),
            '12': self._money_cells(line12_amt, currency),
        }

    def _invoice_line_values(self, move, source):
        partner = move.partner_id.with_company(move.company_id)
        return {
            'date': fields.Date.to_string(move.invoice_date or move.date),
            'doc_no': move.name,
            'partner': partner.name or '',
            'tax_id': partner.vat or '',
            'base': move.amount_untaxed_signed,
            'vat': move.amount_tax_signed,
            'total': move.amount_total_signed,
            'source': source,
        }

    def _prepare_report_data(self):
        self.ensure_one()
        if self.date_from > self.date_to:
            raise UserError(_('Start date must be before end date.'))
        if self.date_from.month != self.date_to.month or self.date_from.year != self.date_to.year:
            raise UserError(_('PP30 must be generated for a single tax month.'))

        company = self.company_id
        currency = company.currency_id
        utc_from, utc_to = self._local_to_utc_range()
        tax_month = self.date_from.month
        tax_year_be = self.date_from.year + 543

        sales_moves = self.env['account.move'].search([
            ('company_id', '=', company.id),
            ('move_type', 'in', ['out_invoice', 'out_refund']),
            ('state', '=', 'posted'),
            ('invoice_date', '>=', self.date_from),
            ('invoice_date', '<=', self.date_to),
        ], order='invoice_date, name')

        purchase_moves = self.env['account.move'].search([
            ('company_id', '=', company.id),
            ('move_type', 'in', ['in_invoice', 'in_refund']),
            ('state', '=', 'posted'),
            ('invoice_date', '>=', self.date_from),
            ('invoice_date', '<=', self.date_to),
        ], order='invoice_date, name')

        pos_orders = self.env['pos.order'].search([
            ('company_id', '=', company.id),
            ('config_id.enable_two_book', '=', True),
            ('date_order', '>=', utc_from),
            ('date_order', '<=', utc_to),
            ('state', '!=', 'cancel'),
        ])
        pos_invoiced = pos_orders.filtered(
            lambda o: o.is_vat_order and o.account_move and o.account_move.state == 'posted'
        )
        pos_pending = pos_orders.filtered(
            lambda o: o.is_vat_order and not o.account_move and o.state in ('paid', 'done')
        )
        pos_non_vat = pos_orders.filtered(lambda o: not o.is_vat_order)
        pos_move_ids = set(pos_invoiced.mapped('account_move').ids)

        sales_lines = self._aggregate_sales(sales_moves, currency)
        purchase_lines = self._aggregate_purchases(purchase_moves, currency)
        net_lines = self._compute_net_lines(sales_lines, purchase_lines, currency)

        output_lines = []
        for move in sales_moves:
            source = _('POS VAT') if move.id in pos_move_ids else _('Other Sales')
            output_lines.append(self._invoice_line_values(move, source))

        input_lines = [
            self._invoice_line_values(move, _('Purchase'))
            for move in purchase_moves
        ]

        pending_lines = []
        for order in pos_pending:
            pending_lines.append({
                'date': fields.Date.to_string(order.date_order + timedelta(hours=7)),
                'doc_no': order.name,
                'partner': order.partner_id.name or '',
                'tax_id': order.partner_id.vat or '',
                'base': order.amount_untaxed,
                'vat': order.amount_tax,
                'total': order.amount_total,
            })

        pp30_lines = {
            **sales_lines,
            **purchase_lines,
            **net_lines,
        }
        for idx in ('13', '14', '15', '16'):
            pp30_lines[idx] = self._money_cells(0.0, currency)

        return {
            'form_code': 'ภ.พ.30',
            'form_revision': '2568',
            'company_name': company.name,
            'company_vat': company.vat or '',
            'company_vat_digits': self._vat_digits(company.vat),
            'branch_digits': self._branch_digits(self.branch_code),
            'address': self._company_address(company),
            'tax_month': tax_month,
            'tax_year_be': tax_year_be,
            'tax_months': [
                {'num': num, 'name': name, 'selected': num == tax_month}
                for num, name in THAI_MONTHS
            ],
            'tax_month_rows': [
                [{'num': num, 'name': name, 'selected': num == tax_month} for num, name in THAI_MONTHS[0:4]],
                [{'num': num, 'name': name, 'selected': num == tax_month} for num, name in THAI_MONTHS[4:8]],
                [{'num': num, 'name': name, 'selected': num == tax_month} for num, name in THAI_MONTHS[8:12]],
            ],
            'filing_normal': self.filing_normal,
            'supplementary_no': self.supplementary_no or 0,
            'date_from': fields.Date.to_string(self.date_from),
            'date_to': fields.Date.to_string(self.date_to),
            'pp30_lines': pp30_lines,
            'output_lines': output_lines,
            'input_lines': input_lines,
            'pending_lines': pending_lines,
            'pos_non_vat_total': self._money_cells(sum(pos_non_vat.mapped('amount_total')), currency),
            'pos_vat_pending_count': len(pos_pending),
            'pos_vat_invoiced_count': len(pos_invoiced),
        }

    def action_print(self):
        self.ensure_one()
        report_data = self._prepare_report_data()
        pdf_bytes = TwoBookPP30PdfBuilder.build(report_data)
        filename = 'PP30_%s_%s.pdf' % (self.date_from, self.date_to)
        attachment = self.env['ir.attachment'].sudo().create({
            'name': filename,
            'type': 'binary',
            'datas': base64.b64encode(pdf_bytes),
            'mimetype': 'application/pdf',
            'res_model': self._name,
            'res_id': self.id,
        })
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s/%s?download=false' % (attachment.id, filename),
            'target': 'new',
        }

# -*- coding: utf-8 -*-
from calendar import monthrange
from datetime import datetime, time, timedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError


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

    def _local_to_utc_range(self):
        self.ensure_one()
        local_dt_from = datetime.combine(self.date_from, time.min)
        local_dt_to = datetime.combine(self.date_to, time.max)
        return local_dt_from - timedelta(hours=7), local_dt_to - timedelta(hours=7)

    def _format_amount(self, amount, currency):
        return '{:,.2f}'.format(currency.round(amount))

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

        company = self.company_id
        currency = company.currency_id
        utc_from, utc_to = self._local_to_utc_range()

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
        output_lines = []
        output_base = output_vat = 0.0
        for move in sales_moves:
            source = _('POS VAT') if move.id in pos_move_ids else _('Other Sales')
            line_vals = self._invoice_line_values(move, source)
            output_lines.append(line_vals)
            output_base += line_vals['base']
            output_vat += line_vals['vat']

        input_lines = []
        input_base = input_vat = 0.0
        for move in purchase_moves:
            line_vals = self._invoice_line_values(move, _('Purchase'))
            input_lines.append(line_vals)
            input_base += line_vals['base']
            input_vat += line_vals['vat']

        pending_lines = []
        pending_base = pending_vat = 0.0
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
            pending_base += order.amount_untaxed
            pending_vat += order.amount_tax

        net_vat = output_vat - input_vat
        return {
            'company_name': company.name,
            'company_vat': company.vat or '',
            'date_from': fields.Date.to_string(self.date_from),
            'date_to': fields.Date.to_string(self.date_to),
            'currency_symbol': currency.symbol or 'THB',
            'output_lines': output_lines,
            'output_base': output_base,
            'output_vat': output_vat,
            'output_base_fmt': self._format_amount(output_base, currency),
            'output_vat_fmt': self._format_amount(output_vat, currency),
            'input_lines': input_lines,
            'input_base': input_base,
            'input_vat': input_vat,
            'input_base_fmt': self._format_amount(input_base, currency),
            'input_vat_fmt': self._format_amount(input_vat, currency),
            'net_vat': net_vat,
            'net_vat_fmt': self._format_amount(net_vat, currency),
            'pos_non_vat_total': sum(pos_non_vat.mapped('amount_total')),
            'pos_non_vat_total_fmt': self._format_amount(sum(pos_non_vat.mapped('amount_total')), currency),
            'pos_vat_invoiced_count': len(pos_invoiced),
            'pos_vat_pending_count': len(pos_pending),
            'pending_lines': pending_lines,
            'pending_base': pending_base,
            'pending_vat': pending_vat,
            'pending_base_fmt': self._format_amount(pending_base, currency),
            'pending_vat_fmt': self._format_amount(pending_vat, currency),
        }

    def action_print(self):
        self.ensure_one()
        report_data = self._prepare_report_data()
        report = self.env.ref('two_book.action_two_book_pp30_report')
        return report.report_action(self.ids, data={'report_data': report_data})

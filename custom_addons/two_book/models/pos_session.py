# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.tools import float_is_zero

from .db_utils import ensure_m2o_column


class PosSession(models.Model):
    _inherit = 'pos.session'

    def init(self):
        super().init()
        ensure_m2o_column(self.env.cr, 'pos_session', 'two_book_vat_move_id')

    two_book_vat_move_id = fields.Many2one(
        'account.move',
        string='Two Book VAT Journal Entry',
        readonly=True,
        copy=False,
    )
    two_book_vat_total = fields.Monetary(
        string='ยอดขาย VAT รวม',
        compute='_compute_two_book_totals',
        currency_field='currency_id',
    )
    two_book_non_vat_total = fields.Monetary(
        string='ยอดขาย Non-VAT รวม',
        compute='_compute_two_book_totals',
        currency_field='currency_id',
    )
    two_book_vat_tax_total = fields.Monetary(
        string='ภาษีขาย (Output VAT) รวม',
        compute='_compute_two_book_totals',
        currency_field='currency_id',
    )

    @api.depends('order_ids', 'order_ids.amount_total', 'order_ids.is_vat_order')
    def _compute_two_book_totals(self):
        for session in self:
            vat_orders = session.order_ids.filtered(
                lambda o: o.is_vat_order and o.state not in ['cancel']
            )
            non_vat_orders = session.order_ids.filtered(
                lambda o: not o.is_vat_order and o.state not in ['cancel']
            )
            session.two_book_vat_total = sum(vat_orders.mapped('amount_total'))
            session.two_book_non_vat_total = sum(non_vat_orders.mapped('amount_total'))
            session.two_book_vat_tax_total = sum(vat_orders.mapped('amount_tax'))

    def _get_closed_orders(self):
        orders = super()._get_closed_orders()
        session_filter = self.env.context.get('two_book_session_filter')
        if not session_filter or not self.config_id.enable_two_book:
            return orders
        if session_filter == 'vat':
            return orders.filtered(lambda o: o.is_vat_order and not o.account_move)
        if session_filter == 'non_vat':
            return orders.filtered(lambda o: not o.is_vat_order)
        return orders

    def _two_book_should_split_session(self):
        self.ensure_one()
        config = self.config_id
        return (
            config.enable_two_book
            and config.two_book_vat_journal_id
            and config.two_book_non_vat_journal_id
            and config.two_book_vat_journal_id != config.two_book_non_vat_journal_id
        )

    def _two_book_run_session_accounting(self, session_filter, journal, bank_payment_method_diffs,
                                         balancing_account=False, amount_to_balance=0):
        self.ensure_one()
        orders = self.with_context(two_book_session_filter=session_filter)._get_closed_orders()
        if not orders:
            return None, {}

        account_move = self.env['account.move'].create({
            'journal_id': journal.id,
            'date': fields.Date.context_today(self),
            'ref': f'{self.name} ({session_filter})',
        })
        previous_move = self.move_id
        self.move_id = account_move

        ctx = {
            'two_book_session_filter': session_filter,
            'two_book_skip_order_sales': session_filter == 'vat',
            'two_book_skip_stock': session_filter == 'vat',
        }
        session = self.with_context(**ctx)

        data = {'bank_payment_method_diffs': bank_payment_method_diffs or {}}
        data = session._accumulate_amounts(data)
        if session_filter == 'vat':
            data = session._two_book_add_vat_clearing_lines(data)
        data = session._create_non_reconciliable_move_lines(data)
        data = session._create_bank_payment_moves(data)
        data = session._create_pay_later_receivable_lines(data)
        data = session._create_cash_statement_lines_and_cash_move_lines(data)
        data = session._create_invoice_receivable_lines(data)
        if not ctx['two_book_skip_stock']:
            data = session._create_stock_valuation_lines(data)
        if balancing_account and amount_to_balance and session_filter == 'non_vat':
            data = session._create_balancing_line(data, balancing_account, amount_to_balance)

        self.move_id = previous_move
        return account_move, data

    def _create_account_move(self, balancing_account=False, amount_to_balance=0, bank_payment_method_diffs=None):
        if not self._two_book_should_split_session():
            return super()._create_account_move(
                balancing_account, amount_to_balance, bank_payment_method_diffs
            )

        bank_payment_method_diffs = bank_payment_method_diffs or {}
        combined_data = {}
        non_vat_move, non_vat_data = self._two_book_run_session_accounting(
            'non_vat',
            self.config_id.two_book_non_vat_journal_id,
            bank_payment_method_diffs,
            balancing_account,
            amount_to_balance,
        )
        vat_move, vat_data = self._two_book_run_session_accounting(
            'vat',
            self.config_id.two_book_vat_journal_id,
            bank_payment_method_diffs,
        )

        if not non_vat_move and not vat_move:
            return super()._create_account_move(
                balancing_account, amount_to_balance, bank_payment_method_diffs
            )

        if non_vat_move:
            self.move_id = non_vat_move
            combined_data.update(non_vat_data)
        if vat_move:
            self.two_book_vat_move_id = vat_move
            if not non_vat_move:
                self.move_id = vat_move
            combined_data.update(vat_data)

        return combined_data

    def _two_book_add_vat_clearing_lines(self, data):
        config = self.config_id
        clearing_account = config.two_book_vat_clearing_account_id
        if not clearing_account or not self.move_id:
            return data

        MoveLine = data.get('MoveLine') or self.env['account.move.line'].with_context(
            check_move_validity=False, skip_invoice_sync=True
        )
        currency = self.currency_id
        for order in self._get_closed_orders().filtered(lambda o: o.is_vat_order and not o.account_move):
            amount = order.amount_paid
            if float_is_zero(amount, precision_rounding=currency.rounding):
                continue
            MoveLine.create({
                'name': _('Two Book VAT clearing: %s', order.name),
                'account_id': clearing_account.id,
                'move_id': self.move_id.id,
                'partner_id': order.partner_id.commercial_partner_id.id or False,
                'credit': amount if amount > 0 else 0.0,
                'debit': -amount if amount < 0 else 0.0,
                'currency_id': currency.id,
            })
        return data

    def _validate_session(self, balancing_account=False, amount_to_balance=0, bank_payment_method_diffs=None):
        record = self.ensure_one()
        vat_move = record.two_book_vat_move_id
        result = super()._validate_session(balancing_account, amount_to_balance, bank_payment_method_diffs)
        if record._two_book_should_split_session() and vat_move and vat_move != record.move_id:
            if vat_move.line_ids:
                vat_move.with_company(record.company_id)._post()
            else:
                vat_move.sudo().unlink()
                record.two_book_vat_move_id = False
        return result

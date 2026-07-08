# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.tools import float_is_zero

_logger = logging.getLogger(__name__)


class PosOrder(models.Model):
    _inherit = 'pos.order'

    is_vat_order = fields.Boolean(
        string='ออกใบกำกับภาษี (VAT)',
        default=False,
        help='True = ออกใบกำกับภาษีเต็มรูปแบบ (7%), False = บิลเงินสด / ไม่ออกใบกำกับ',
    )
    two_book_type = fields.Selection([
        ('vat', 'ใบกำกับภาษี (VAT 7%)'),
        ('non_vat', 'บิลเงินสด (Non-VAT)'),
    ], string='ประเภทเอกสาร', compute='_compute_two_book_type', store=True)

    two_book_invoice_status = fields.Selection([
        ('invoiced', 'ออกใบกำกับแล้ว'),
        ('pending', 'รอออกใบกำกับ'),
    ], string='สถานะใบกำกับ', compute='_compute_two_book_invoice_status', store=True, index=True)

    tax_invoice_number = fields.Char(
        string='เลขที่ใบกำกับภาษี',
        readonly=True,
        copy=False,
    )
    amount_untaxed = fields.Monetary(
        string='ยอดก่อนภาษี',
        compute='_compute_amount_untaxed',
        store=True,
        currency_field='currency_id',
    )
    tax_stock_move_ids = fields.One2many(
        'stock.move',
        'two_book_pos_order_id',
        string='Tax Stock Moves',
        domain=[('is_tax_stock_move', '=', True)],
    )
    stock_gap_ids = fields.One2many(
        'two.book.stock.gap',
        'pos_order_id',
        string='Stock Gaps',
    )

    @api.depends('amount_total', 'amount_tax')
    def _compute_amount_untaxed(self):
        for order in self:
            order.amount_untaxed = order.amount_total - order.amount_tax

    @api.depends('is_vat_order')
    def _compute_two_book_type(self):
        for order in self:
            order.two_book_type = 'vat' if order.is_vat_order else 'non_vat'

    @api.depends('account_move', 'state', 'is_vat_order', 'config_id.enable_two_book')
    def _compute_two_book_invoice_status(self):
        for order in self:
            if not order.config_id.enable_two_book or not order.is_vat_order:
                order.two_book_invoice_status = False
                continue
            if order.account_move:
                order.two_book_invoice_status = 'invoiced'
            elif order.state in ('paid', 'done'):
                order.two_book_invoice_status = 'pending'
            else:
                order.two_book_invoice_status = False

    @api.model
    def _load_pos_data_fields(self, config):
        fields_list = list(super()._load_pos_data_fields(config))
        if fields_list and 'is_vat_order' not in fields_list:
            fields_list.append('is_vat_order')
        return fields_list

    def _prepare_invoice_vals(self):
        vals = super()._prepare_invoice_vals()
        config = self.config_id

        if not config.enable_two_book:
            return vals

        if self.is_vat_order:
            if config.two_book_vat_journal_id:
                vals['journal_id'] = config.two_book_vat_journal_id.id
            if config.two_book_vat_fiscal_position_id:
                vals['fiscal_position_id'] = config.two_book_vat_fiscal_position_id.id
        else:
            if config.two_book_non_vat_journal_id:
                vals['journal_id'] = config.two_book_non_vat_journal_id.id
            if config.two_book_non_vat_fiscal_position_id:
                vals['fiscal_position_id'] = config.two_book_non_vat_fiscal_position_id.id

        return vals

    def _two_book_assert_vat_invoice_allowed(self):
        blocked = self.filtered(
            lambda o: o.config_id.enable_two_book and not o.is_vat_order
        )
        if blocked:
            raise UserError(_(
                'Two Book: Non-VAT orders cannot be invoiced (%(orders)s).',
                orders=', '.join(blocked.mapped('name')),
            ))

    def _two_book_release_vat_clearing(self, invoice):
        """Debit VAT clearing created at session close when the tax invoice is posted."""
        orders = self.filtered(
            lambda o: (
                o.config_id.enable_two_book
                and o.is_vat_order
                and o.session_id
                and o.session_id._two_book_should_split_session()
            )
        )
        if not orders:
            return self.env['account.move']

        Move = self.env['account.move'].sudo()
        created_moves = self.env['account.move']
        currency = invoice.currency_id

        for config, config_orders in orders.grouped('config_id').items():
            clearing = config.two_book_vat_clearing_account_id
            if not clearing:
                _logger.warning(
                    'Two Book: missing VAT clearing account on %s — skip release',
                    config.display_name,
                )
                continue

            receivable_lines = invoice.line_ids.filtered(
                lambda line: line.account_id.account_type == 'asset_receivable'
            )
            receivable_account = (
                receivable_lines[:1].account_id
                or invoice.partner_id.with_company(invoice.company_id).property_account_receivable_id
            )
            if not receivable_account:
                raise UserError(_(
                    'Two Book: cannot find receivable account for invoice %(invoice)s.',
                    invoice=invoice.display_name,
                ))

            journal = config.two_book_vat_journal_id or invoice.journal_id
            total = sum(config_orders.mapped('amount_paid'))
            if float_is_zero(total, precision_rounding=currency.rounding):
                continue

            move = Move.create({
                'move_type': 'entry',
                'journal_id': journal.id,
                'date': invoice.invoice_date or fields.Date.context_today(self),
                'ref': _('Two Book VAT clearing release: %s', invoice.name),
                'company_id': invoice.company_id.id,
                'line_ids': [
                    (0, 0, {
                        'name': _('Release VAT clearing (%s)', ', '.join(config_orders.mapped('name'))),
                        'account_id': clearing.id,
                        'partner_id': invoice.partner_id.id,
                        'debit': total if total > 0 else 0.0,
                        'credit': -total if total < 0 else 0.0,
                    }),
                    (0, 0, {
                        'name': _('Release VAT clearing (%s)', invoice.name),
                        'account_id': receivable_account.id,
                        'partner_id': invoice.partner_id.id,
                        'debit': -total if total < 0 else 0.0,
                        'credit': total if total > 0 else 0.0,
                    }),
                ],
            })
            move.action_post()
            created_moves |= move

        return created_moves

    def action_pos_order_invoice(self):
        self._two_book_assert_vat_invoice_allowed()
        res = super().action_pos_order_invoice()
        for order in self:
            if order.account_move:
                order.tax_invoice_number = order.account_move.name
                if order.config_id.enable_two_book and order.is_vat_order:
                    order._two_book_release_vat_clearing(order.account_move)
        return res

    def _create_order_picking(self):
        super()._create_order_picking()
        for order in self:
            if not order.config_id.enable_two_book:
                continue
            if order.is_vat_order:
                order._create_vat_tax_stock_moves()
            else:
                order._record_non_vat_stock_gap()

    def _get_two_book_stockable_lines(self):
        self.ensure_one()
        return self.lines.filtered(
            lambda line: line.product_id.type == 'consu' and not line.product_id.uom_id.is_zero(line.qty)
        )

    def _create_vat_tax_stock_moves(self):
        """Shadow picking: WH/VAT -> Virtual/VAT_Out for VAT orders."""
        self.ensure_one()
        config = self.config_id
        tax_location = config.two_book_tax_location_id
        vat_out_location = config.two_book_vat_out_location_id

        if not tax_location or not vat_out_location:
            _logger.warning(
                'Two Book: missing tax locations on POS config %s — skip tax stock for %s',
                config.display_name,
                self.name,
            )
            return self.env['stock.picking']

        picking_type = config.two_book_tax_picking_type_id
        if not picking_type:
            picking_type = self.env['stock.picking.type'].search([
                ('code', '=', 'internal'),
                ('warehouse_id', '=', config.warehouse_id.id),
            ], limit=1)
        if not picking_type:
            _logger.warning('Two Book: no internal picking type for tax stock on order %s', self.name)
            return self.env['stock.picking']

        stockable_lines = self._get_two_book_stockable_lines().filtered(lambda line: line.qty > 0)
        if not stockable_lines:
            return self.env['stock.picking']

        picking = self.env['stock.picking'].sudo().create({
            'picking_type_id': picking_type.id,
            'location_id': tax_location.id,
            'location_dest_id': vat_out_location.id,
            'origin': self.name,
            'pos_order_id': self.id,
            'pos_session_id': self.session_id.id,
        })

        for line in stockable_lines:
            self.env['stock.move'].sudo().create({
                'name': line.full_product_name or line.product_id.display_name,
                'product_id': line.product_id.id,
                'product_uom_qty': line.qty,
                'product_uom': line.product_uom_id.id,
                'location_id': tax_location.id,
                'location_dest_id': vat_out_location.id,
                'picking_id': picking.id,
                'is_tax_stock_move': True,
                'two_book_pos_order_id': self.id,
            })

        picking.action_confirm()
        for move in picking.move_ids:
            move.quantity = move.product_uom_qty
        try:
            picking.button_validate()
        except UserError as err:
            _logger.warning(
                'Two Book: tax stock validation failed for %s — %s',
                self.name,
                err,
            )
            picking.action_cancel()
            self._record_non_vat_stock_gap(message='tax_stock_failed')

        return picking

    def _record_non_vat_stock_gap(self, message=None):
        """Record gap when Non-VAT sale does not deduct WH/VAT."""
        self.ensure_one()
        Gap = self.env['two.book.stock.gap'].sudo()
        existing_products = set(self.stock_gap_ids.mapped('product_id').ids)
        for line in self._get_two_book_stockable_lines().filtered(lambda l: l.qty > 0):
            if line.product_id.id in existing_products:
                continue
            Gap.create({
                'pos_order_id': self.id,
                'product_id': line.product_id.id,
                'quantity': line.qty,
                'state': 'open',
            })
        if message:
            _logger.info('Two Book gap recorded for %s (%s)', self.name, message)

    def get_two_book_merge_invoice_vals(self):
        """Defaults for merged VAT invoice (used by pos_merge_invoice)."""
        self.ensure_one()
        config = self.config_id
        vals = {}
        if config.two_book_vat_journal_id:
            vals['journal_id'] = config.two_book_vat_journal_id.id
        if config.two_book_vat_fiscal_position_id:
            vals['fiscal_position_id'] = config.two_book_vat_fiscal_position_id.id
        return vals

    def _two_book_skip_session_sales(self):
        self.ensure_one()
        return (
            self.env.context.get('two_book_skip_order_sales')
            and self.config_id.enable_two_book
            and self.is_vat_order
            and not self.account_move
        )

    def _prepare_tax_base_line_values(self):
        if self._two_book_skip_session_sales():
            return []
        return super()._prepare_tax_base_line_values()


class PosOrderLine(models.Model):
    _inherit = 'pos.order.line'

    two_book_invoice_status = fields.Selection(
        related='order_id.two_book_invoice_status',
        string='สถานะใบกำกับ',
        store=True,
        readonly=True,
    )
    two_book_order_ref = fields.Char(
        related='order_id.name',
        string='Order Ref',
        store=True,
        readonly=True,
    )
    two_book_line_untaxed = fields.Monetary(
        string='ยอดก่อนภาษี',
        compute='_compute_two_book_line_amounts',
        currency_field='currency_id',
        store=True,
    )
    two_book_line_tax = fields.Monetary(
        string='ภาษี',
        compute='_compute_two_book_line_amounts',
        currency_field='currency_id',
        store=True,
    )

    @api.depends('price_subtotal', 'price_subtotal_incl')
    def _compute_two_book_line_amounts(self):
        for line in self:
            line.two_book_line_untaxed = line.price_subtotal
            line.two_book_line_tax = line.price_subtotal_incl - line.price_subtotal

    def _get_tax_ids_after_fiscal_position(self):
        order = self.order_id
        config = order.config_id

        if (
            config.enable_two_book
            and not order.is_vat_order
            and config.two_book_non_vat_fiscal_position_id
        ):
            return config.two_book_non_vat_fiscal_position_id.map_tax(self.tax_ids)

        if (
            config.enable_two_book
            and order.is_vat_order
            and config.two_book_vat_fiscal_position_id
        ):
            return config.two_book_vat_fiscal_position_id.map_tax(self.tax_ids)

        return super()._get_tax_ids_after_fiscal_position()

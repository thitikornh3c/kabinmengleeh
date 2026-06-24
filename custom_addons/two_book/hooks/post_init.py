# -*- coding: utf-8 -*-
import logging

_logger = logging.getLogger(__name__)


def post_init_hook(env):
    _setup_fiscal_position_tax_maps(env)
    _assign_pos_config_defaults(env)


def _setup_fiscal_position_tax_maps(env):
    non_vat_fp = env.ref('two_book.fiscal_position_non_vat_th', raise_if_not_found=False)
    if not non_vat_fp:
        return

    FPTax = env['account.fiscal.position.tax']
    for company in env.companies:
        sale_taxes = env['account.tax'].search([
            ('company_id', '=', company.id),
            ('type_tax_use', '=', 'sale'),
            ('amount', '>', 0),
        ])
        zero_tax = env['account.tax'].search([
            ('company_id', '=', company.id),
            ('type_tax_use', '=', 'sale'),
            ('amount', '=', 0),
        ], limit=1)
        if not sale_taxes or not zero_tax:
            _logger.info(
                'Two Book: skip FP tax map for %s (sale taxes or zero tax missing)',
                company.name,
            )
            continue
        fp = non_vat_fp.with_company(company)
        for tax in sale_taxes:
            if FPTax.search_count([
                ('position_id', '=', fp.id),
                ('tax_src_id', '=', tax.id),
            ]):
                continue
            FPTax.create({
                'position_id': fp.id,
                'tax_src_id': tax.id,
                'tax_dest_id': zero_tax.id,
            })


def _assign_pos_config_defaults(env):
    tax_loc = env.ref('two_book.stock_location_wh_vat', raise_if_not_found=False)
    vat_out = env.ref('two_book.stock_location_vat_out', raise_if_not_found=False)
    fp_vat = env.ref('two_book.fiscal_position_vat_th', raise_if_not_found=False)
    fp_non = env.ref('two_book.fiscal_position_non_vat_th', raise_if_not_found=False)
    journal_non = env.ref('two_book.journal_non_vat_sales', raise_if_not_found=False)
    clearing = env.ref('two_book.account_vat_clearing', raise_if_not_found=False)

    for config in env['pos.config'].search([]):
        vals = {}
        if tax_loc and not config.two_book_tax_location_id:
            vals['two_book_tax_location_id'] = tax_loc.id
        if vat_out and not config.two_book_vat_out_location_id:
            vals['two_book_vat_out_location_id'] = vat_out.id
        if fp_vat and not config.two_book_vat_fiscal_position_id:
            vals['two_book_vat_fiscal_position_id'] = fp_vat.id
        if fp_non and not config.two_book_non_vat_fiscal_position_id:
            vals['two_book_non_vat_fiscal_position_id'] = fp_non.id
        if journal_non and not config.two_book_non_vat_journal_id:
            vals['two_book_non_vat_journal_id'] = journal_non.id
        if clearing and not config.two_book_vat_clearing_account_id:
            vals['two_book_vat_clearing_account_id'] = clearing.id
        if not config.two_book_vat_journal_id:
            sale_journal = env['account.journal'].search([
                ('type', '=', 'sale'),
                ('company_id', '=', config.company_id.id),
            ], limit=1)
            if sale_journal:
                vals['two_book_vat_journal_id'] = sale_journal.id
        if vals:
            config.write(vals)

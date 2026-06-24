# -*- coding: utf-8 -*-
import logging

_logger = logging.getLogger(__name__)


def post_init_hook(env):
    _ensure_vat_clearing_accounts(env)
    _setup_fiscal_position_tax_maps(env)
    _assign_pos_config_defaults(env)


def _ensure_vat_clearing_accounts(env):
    """Create VAT clearing account per company (safer than XML on Odoo.sh)."""
    Account = env['account.account'].sudo()
    IrModelData = env['ir.model.data'].sudo()

    for company in env.companies:
        existing = Account.search([
            ('code', '=', 'VATCLR'),
            ('company_id', '=', company.id),
        ], limit=1)
        if existing:
            _ensure_xmlid(IrModelData, 'two_book.account_vat_clearing', existing)
            continue
        try:
            account = Account.create({
                'code': 'VATCLR',
                'name': 'พักรายได้ VAT รอออกใบกำกับ',
                'account_type': 'liability_current',
                'reconcile': True,
                'company_id': company.id,
            })
            _ensure_xmlid(IrModelData, 'two_book.account_vat_clearing', account)
        except Exception as err:
            _logger.warning(
                'Two Book: could not create VAT clearing account for %s: %s',
                company.name,
                err,
            )


def _ensure_xmlid(ir_model_data, xml_name, record):
    module, name = xml_name.split('.')
    existing = ir_model_data.search([
        ('module', '=', module),
        ('name', '=', name),
    ], limit=1)
    if existing:
        return
    ir_model_data.create({
        'name': name,
        'module': module,
        'model': record._name,
        'res_id': record.id,
        'noupdate': True,
    })


def _get_clearing_account(env, company):
    account = env.ref('two_book.account_vat_clearing', raise_if_not_found=False)
    if account and account.company_id == company:
        return account
    return env['account.account'].search([
        ('code', '=', 'VATCLR'),
        ('company_id', '=', company.id),
    ], limit=1)


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

    for config in env['pos.config'].search([]):
        vals = {}
        company = config.company_id
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
        clearing = _get_clearing_account(env, company)
        if clearing and not config.two_book_vat_clearing_account_id:
            vals['two_book_vat_clearing_account_id'] = clearing.id
        if not config.two_book_vat_journal_id:
            sale_journal = env['account.journal'].search([
                ('type', '=', 'sale'),
                ('company_id', '=', company.id),
            ], limit=1)
            if sale_journal:
                vals['two_book_vat_journal_id'] = sale_journal.id
        if vals:
            config.write(vals)

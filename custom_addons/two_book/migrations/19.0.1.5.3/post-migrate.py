# -*- coding: utf-8 -*-
from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    from odoo.addons.two_book.hooks.post_init import _ensure_pp30_menus
    _ensure_pp30_menus(env)

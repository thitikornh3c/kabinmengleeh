import math
from odoo import models, fields, api

class CustomAccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    @api.depends('move_id', 'tax_line_ids.amount')
    def _compute_tax_amount(self):
        for line in self:
            if line.tax_line_ids:
                for tax in line.tax_line_ids:
                    # Round down the tax amount to 2 decimal places
                    if tax.amount:
                        tax.amount = math.floor(tax.amount * 100) / 100

class AccountMove(models.Model):
    _inherit = 'account.move'

    bank_no = fields.Char(related='company_id.x_studio_bankno', string="Bank No", store=False)
    # bank_no = fields.Char(related='company_id.bank_no', string="Bank No", store=False)
    amount_total_words = fields.Char(compute='_compute_amount_total_words', store=False)

    def _compute_amount_total_words(self):
        for record in self:
            record.amount_total_words = self.amount_to_words(record.amount_total)

    def amount_to_words(self, amount):
        units = ["", "หนึ่ง", "สอง", "สาม", "สี่", "ห้า", "หก", "เจ็ด", "แปด", "เก้า"]
        teens = ["สิบ", "สิบเอ็ด", "สิบสอง", "สิบสาม", "สิบสี่", "สิบห้า", "สิบหก", "สิบเจ็ด", "สิบแปด", "สิบเก้า"]
        tens = ["", "สิบ", "ยี่สิบ", "สามสิบ", "สี่สิบ", "ห้าสิบ", "หกสิบ", "เจ็ดสิบ", "แปดสิบ", "เก้าสิบ"]
        thousands = ["", "พัน", "หมื่น", "แสน", "ล้าน"]

        def convert_integer(n):
            if n == 0:
                return "ศูนย์"
            words = []
            if n >= 1000000:
                words.append(units[n // 1000000] + "ล้าน")
                n %= 1000000
            if n >= 100000:
                words.append(units[n // 100000] + "แสน")
                n %= 100000
            if n >= 10000:
                words.append(units[n // 10000] + "หมื่น")
                n %= 10000
            if n >= 1000:
                words.append(units[n // 1000] + "พัน")
                n %= 1000
            if n >= 100:
                words.append(units[n // 100] + "ร้อย")
                n %= 100
            if n >= 20:
                words.append(tens[n // 10])
                n %= 10
            if 10 <= n < 20:
                words.append(teens[n - 10])
                n = 0
            if n > 0:
                words.append(units[n])
            return ''.join(words)

        def convert_fraction(n):
            if n == 0:
                return ""
            words = []
            if n >= 10:
                words.append(tens[n // 10])
                n %= 10
            if n > 0:
                words.append(units[n])
            return ''.join(words)

        integer_part = int(amount)
        fraction_part = int(round((amount - integer_part) * 100))

        integer_words = convert_integer(integer_part)
        fraction_words = convert_fraction(fraction_part)

        if fraction_part > 0:
            return f"{integer_words}บาท{fraction_words}สตางค์"
        else:
            return f"{integer_words}บาทถ้วน"


    @api.depends('invoice_line_ids.price_subtotal', 'tax_line_ids.amount')
    def _compute_amount(self):
        super(AccountMove, self)._compute_amount()
        
        # Custom rounding logic for tax amount
        for move in self:
            for line in move.invoice_line_ids:
                for tax in line.tax_ids:
                    if tax.amount:
                        # Round down the tax amount to 2 decimal places
                        tax.amount = math.floor(tax.amount * 100) / 100
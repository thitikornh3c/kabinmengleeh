from odoo import models, fields

class AccountMove(models.Model):
    _inherit = 'account.move'

    amount_total_words = fields.Char(compute='_compute_amount_total_words', store=False)

    def _compute_amount_total_words(self):
        for record in self:
            record.amount_total_words = self.amount_to_words(record.amount_total)

    def amount_to_words(self, amount):
        units = ["", "หนึ่ง", "สอง", "สาม", "สี่", "ห้า", "หก", "เจ็ด", "แปด", "เก้า"]
        teens = ["สิบ", "สิบเอ็ด", "สิบสอง", "สิบสาม", "สิบสี่", "สิบห้า", "สิบหก", "สิบเจ็ด", "สิบแปด", "สิบเก้า"]
        tens = ["", "สิบ", "ยี่สิบ", "สามสิบ", "สี่สิบ", "ห้าสิบ", "หกสิบ", "เจ็ดสิบ", "แปดสิบ", "เก้าสิบ"]

        def convert_integer(n):
            if n == 0:
                return "ศูนย์"
            words = []
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
            return f"{integer_words}บาท{fraction_words}สตางค์ถ้วน"
        else:
            return f"{integer_words}บาทถ้วน"

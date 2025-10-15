from odoo import models, fields

class AccountMove(models.Model):
    _inherit = 'account.move'

    bank_no = fields.Char(related='company_id.x_studio_bankno', string="Bank No", store=False)
    amount_total_words = fields.Char(compute='_compute_amount_total_words', store=False)

    def _compute_amount_total_words(self):
        for record in self:
            lang = record.partner_id.lang or 'th_TH'  # default to Thai
            record.amount_total_words = self.amount_to_words(record.amount_total, lang)

    def amount_to_words(self, amount, lang='th_TH'):
        """
        Convert amount to words based on language.
        lang: 'th_TH' for Thai, 'en_US' for English
        """
        if lang.startswith('en'):
            # ภาษาอังกฤษ
            return self.amount_to_words_en(amount)
        else:
            # ภาษาไทย
            return self.amount_to_words_th(amount)

    def amount_to_words_th(self, amount):
        units = ["", "หนึ่ง", "สอง", "สาม", "สี่", "ห้า", "หก", "เจ็ด", "แปด", "เก้า"]
        teens = ["สิบ", "สิบเอ็ด", "สิบสอง", "สิบสาม", "สิบสี่", "สิบห้า", "สิบหก", "สิบเจ็ด", "สิบแปด", "สิบเก้า"]
        tens = ["", "สิบ", "ยี่สิบ", "สามสิบ", "สี่สิบ", "ห้าสิบ", "หกสิบ", "เจ็ดสิบ", "แปดสิบ", "เก้าสิบ"]

        def convert_integer(n):
            if n == 0:
                return "ศูนย์"
            words = []
            thousands = ["", "พัน", "หมื่น", "แสน", "ล้าน"]
            unit_idx = 0
            while n > 0:
                part = n % 10
                if unit_idx == 0 and part == 1 and n > 10:
                    words.insert(0, "เอ็ด")
                elif unit_idx == 1 and part > 0:
                    if part == 1:
                        words.insert(0, "สิบ")
                    elif part == 2:
                        words.insert(0, "ยี่สิบ")
                    else:
                        words.insert(0, units[part] + "สิบ")
                elif part > 0:
                    words.insert(0, units[part] + (thousands[unit_idx] if unit_idx < len(thousands) else ""))
                n //= 10
                unit_idx += 1
            return ''.join(words)

        integer_part = int(amount)
        fraction_part = int(round((amount - integer_part) * 100))
        integer_words = convert_integer(integer_part)
        fraction_words = ''
        if fraction_part > 0:
            fraction_words = self.amount_to_words_th(fraction_part)
            return f"{integer_words}บาท{fraction_words}สตางค์"
        else:
            return f"{integer_words}บาทถ้วน"

    def amount_to_words_en(self, amount):
        units = ["","One","Two","Three","Four","Five","Six","Seven","Eight","Nine"]
        teens = ["Ten","Eleven","Twelve","Thirteen","Fourteen","Fifteen",
                "Sixteen","Seventeen","Eighteen","Nineteen"]
        tens = ["","","Twenty","Thirty","Forty","Fifty","Sixty","Seventy","Eighty","Ninety"]
        thousands = ["","Thousand","Million","Billion"]

        def convert_hundred(n):
            word = ""
            if n >= 100:
                word += units[n//100] + " Hundred "
                n %= 100
            if 10 <= n < 20:
                word += teens[n-10] + " "
            else:
                if n >= 20:
                    word += tens[n//10] + " "
                    n %= 10
                if n > 0:
                    word += units[n] + " "
            return word.strip()

        if amount == 0:
            return "Zero Baht"

        integer_part = int(amount)
        fraction_part = int(round((amount - integer_part) * 100))
        words = []
        i = 0
        while integer_part > 0:
            n = integer_part % 1000
            if n != 0:
                words.insert(0, convert_hundred(n) + (" " + thousands[i] if i>0 else ""))
            integer_part //= 1000
            i += 1
        result = " ".join(words) + " Baht net"
        if fraction_part > 0:
            fraction_words = self.amount_to_words_th(fraction_part)
            return f"{result}Baht {fraction_words} Satang"
        else:
            return f"{result} Baht net"
        # if fraction_part > 0:
        #     result += f" and {convert_hundred(fraction_part)} Satang"
        # return result

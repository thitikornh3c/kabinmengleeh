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

        def convert_number(n):
            n = int(n)
            digit = ["", "สิบ", "ร้อย", "พัน", "หมื่น", "แสน"]
            word = ""
            num_str = str(n)
            num_len = len(num_str)
            for i, c in enumerate(num_str):
                num = int(c)
                pos = num_len - i - 1
                if num == 0:
                    continue
                if pos == 0:
                    if num == 1 and num_len > 1:
                        word += "เอ็ด"
                    else:
                        word += units[num]
                elif pos == 1:
                    if num == 1:
                        word += "สิบ"
                    elif num == 2:
                        word += "ยี่สิบ"
                    else:
                        word += units[num] + "สิบ"
                else:
                    word += units[num] + digit[pos]
            return word

        def thai_number(n):
            n = int(n)
            if n == 0:
                return "ศูนย์"
            parts = []
            group = 0
            while n > 0:
                part = n % 1000000
                n //= 1000000
                if part > 0:
                    text = convert_number(part)
                    if group > 0:
                        text += "ล้าน"
                    parts.insert(0, text)
                group += 1
            return ''.join(parts)

        integer_part = int(amount)
        fraction_part = int(round((amount - integer_part) * 100))

        integer_words = thai_number(integer_part)
        if fraction_part > 0:
            fraction_words = thai_number(fraction_part)
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
        result = " ".join(words)
        if fraction_part > 0:
            fraction_words = self.amount_to_words_th(fraction_part)
            return f"{result}Baht {fraction_words} Satang"
        else:
            return f"{result} Baht net"
        # if fraction_part > 0:
        #     result += f" and {convert_hundred(fraction_part)} Satang"
        # return result

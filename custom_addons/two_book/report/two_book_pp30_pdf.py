# -*- coding: utf-8 -*-
import io
import logging
import re

from odoo.tools.misc import file_path

_logger = logging.getLogger(__name__)

try:
    from pdfrw import PdfDict, PdfName, PdfObject, PdfReader, PdfString, PdfWriter
except ImportError:  # pragma: no cover - Odoo.sh installs pdfrw via requirements.txt
    PdfDict = PdfName = PdfObject = PdfReader = PdfString = PdfWriter = None

PP30_LINE_FIELDS = {
    '1': 'Text2.1',
    '2': 'Text2.2',
    '3': 'Text2.3',
    '4': 'Text2.4',
    '5': 'Text2.5',
    '6': 'Text2.6',
    '7': 'Text2.7',
    '8': 'Text2.8',
    '9': 'Text2.9',
    '10': 'Text2.10',
    '11': 'Text2.11',
    '12': 'Text2.12',
    '13': 'Text2.13',
    '14': 'Text2.14',
    '15': 'Text2.15',
    '16': 'Text2.16',
}


class TwoBookPP30PdfBuilder:
    TEMPLATE_PATH = 'two_book/static/pdf/pp30_010968.pdf'

    @classmethod
    def build(cls, report_data):
        if PdfReader is None or PdfWriter is None:
            raise RuntimeError('pdfrw is required to print PP30. Add pdfrw to requirements.txt.')

        template_path = file_path(cls.TEMPLATE_PATH)
        pdf = PdfReader(template_path)
        field_values = cls._build_field_values(report_data)
        cls._fill_acroform(pdf, field_values)

        output = io.BytesIO()
        PdfWriter().write(output, pdf)
        return output.getvalue()

    @classmethod
    def _fill_acroform(cls, pdf, field_values):
        acroform = pdf.Root.AcroForm
        if not acroform or not acroform.Fields:
            raise RuntimeError('PP30 template has no AcroForm fields.')

        acroform.update(PdfDict(NeedAppearances=PdfObject('true')))
        cls._walk_fields(acroform.Fields, field_values)

    @classmethod
    def _walk_fields(cls, fields, field_values, prefix=''):
        for field in fields or []:
            name = cls._field_name(field.T)
            full_name = '.'.join(part for part in (prefix, name) if part)

            if field.Kids:
                if full_name in field_values and cls._is_button_group(field):
                    cls._set_button_group(field, field_values[full_name])
                else:
                    cls._walk_fields(field.Kids, field_values, full_name)
                continue

            if full_name not in field_values:
                continue

            value = field_values[full_name]
            if field.FT == PdfName('Btn') or cls._is_button_group(field):
                cls._set_button_group(field, value)
            else:
                cls._set_text_field(field, value)

    @staticmethod
    def _field_name(field_t):
        if not field_t:
            return ''
        name = str(field_t)
        if name.startswith('(') and name.endswith(')'):
            return name[1:-1]
        return name

    @staticmethod
    def _is_button_group(field):
        return field.FT == PdfName('Btn') or (field.Kids and not field.FT)

    @staticmethod
    def _set_text_field(field, value):
        if value in (None, ''):
            return
        field.V = PdfString.encode(str(value))

    @classmethod
    def _set_button_group(cls, field, value):
        if value in (None, ''):
            return
        state = str(value)
        if not state.startswith('/'):
            state = '/%s' % state
        state_name = PdfName(state[1:])

        field.V = state_name
        if not field.Kids:
            field.AS = state_name
            return

        for kid in field.Kids:
            selected = PdfName('Off')
            if kid.AP and kid.AP.N:
                for appearance in kid.AP.N.keys():
                    if str(appearance) == state:
                        selected = appearance
                        break
            kid.AS = selected
            if selected != PdfName('Off'):
                kid.V = state_name

    @classmethod
    def _build_field_values(cls, report_data):
        address = report_data.get('address') or {}
        pp30_lines = report_data.get('pp30_lines') or {}
        zip_code = re.sub(r'\D', '', address.get('zip') or '')

        values = {
            'Text1.0': re.sub(r'\D', '', report_data.get('company_vat') or ''),
            'Text1.1': ''.join(report_data.get('branch_digits') or []),
            'Text1.01': report_data.get('company_name') or '',
            'Text1.02': report_data.get('company_name') or '',
            'Text1.3': address.get('building') or '',
            'Text1.4': address.get('number') or '',
            'Text1.5': address.get('moo') or '',
            'Text1.6': address.get('soi') or '',
            'Text1.7': address.get('road') or '',
            'Text1.8': address.get('subdistrict') or '',
            'Text1.9': address.get('district') or '',
            'Text1.10': address.get('province') or '',
            'Text1.13': zip_code,
            'Text1.16': address.get('phone') or '',
            'Text2.19': str(report_data.get('tax_year_be') or ''),
            'Text2.20': str(report_data.get('tax_year_be') or ''),
            'Radio Button3': '/%s' % max(0, min(11, (report_data.get('tax_month') or 1) - 1)),
            'Radio Button4': '/0',
            'Radio Button5': '/0',
            'Radio Button6': '/0',
        }

        if report_data.get('filing_normal', True):
            values['Radio Button7'] = '/0'
        else:
            values['Radio Button7'] = '/1'
            supplementary = str(report_data.get('supplementary_no') or '')
            values.update({
                'Text2.22': supplementary,
                'Text2.23': supplementary,
            })

        for line_no, field_name in PP30_LINE_FIELDS.items():
            line = pp30_lines.get(line_no) or {}
            values[field_name] = cls._format_line_amount(line)

        return values

    @staticmethod
    def _format_line_amount(line):
        baht = line.get('baht') or 0
        satang = line.get('satang') or 0
        sign = -1 if baht < 0 else 1
        absolute_baht = abs(int(baht))
        if satang:
            return f'{sign * absolute_baht}.{int(satang):02d}'
        return str(sign * absolute_baht)

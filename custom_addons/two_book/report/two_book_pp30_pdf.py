# -*- coding: utf-8 -*-
import io
import logging
import re

from odoo.tools.misc import file_path

_logger = logging.getLogger(__name__)

try:
    from PyPDF2 import PdfReader, PdfWriter
except ImportError:  # pragma: no cover - Odoo.sh installs PyPDF2 via requirements.txt
    PdfReader = PdfWriter = None

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
            raise RuntimeError('PyPDF2 is required to print PP30. Add PyPDF2 to requirements.txt.')

        template_path = file_path(cls.TEMPLATE_PATH)
        reader = PdfReader(template_path)
        writer = cls._clone_reader(reader)
        field_values = cls._build_field_values(report_data)

        for page in writer.pages:
            cls._update_page_fields(writer, page, field_values)

        cls._set_need_appearances(writer)

        output = io.BytesIO()
        writer.write(output)
        return output.getvalue()

    @staticmethod
    def _clone_reader(reader):
        writer = PdfWriter()
        if hasattr(writer, 'append'):
            writer.append(reader)
            return writer
        if hasattr(writer, 'clone_reader_document_root'):
            writer.clone_reader_document_root(reader)
            return writer
        if hasattr(writer, 'appendPagesFromReader'):
            writer.appendPagesFromReader(reader)
            return writer
        for page in reader.pages:
            writer.add_page(page)
        return writer

    @staticmethod
    def _update_page_fields(writer, page, field_values):
        if hasattr(writer, 'update_page_form_field_values'):
            try:
                writer.update_page_form_field_values(page, field_values, auto_regenerate=False)
                return
            except TypeError:
                writer.update_page_form_field_values(page, field_values)
                return
        if hasattr(writer, 'updatePageFormFieldValues'):
            writer.updatePageFormFieldValues(page, field_values)
            return
        raise RuntimeError('PyPDF2 version does not support PDF form field updates.')

    @staticmethod
    def _set_need_appearances(writer):
        if hasattr(writer, 'set_need_appearances_writer'):
            try:
                writer.set_need_appearances_writer(True)
                return
            except TypeError:
                writer.set_need_appearances_writer()
                return
        try:
            from PyPDF2.generic import BooleanObject, NameObject
            root = writer._root_object  # pylint: disable=protected-access
            if '/AcroForm' in root:
                root['/AcroForm'].update({
                    NameObject('/NeedAppearances'): BooleanObject(True),
                })
        except Exception as err:
            _logger.debug('Two Book PP30: skip NeedAppearances flag: %s', err)

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

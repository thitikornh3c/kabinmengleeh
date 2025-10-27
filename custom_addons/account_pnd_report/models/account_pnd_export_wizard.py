import requests
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime
from odoo.tools import date_utils
import io
import csv
import logging
from PyPDF2 import PdfReader, PdfWriter
from odoo.modules.module import get_module_resource

_logger = logging.getLogger(__name__)

class AccountPNDExportWizard(models.TransientModel):
    _name = 'account.pnd.export.wizard'
    _description = 'Account PND Report Date Range Export Wizard'

    # Step 2 fields
    date_from = fields.Date(
        string='Date From', 
        required=True, 
        default=lambda self: date_utils.start_of(fields.Date.context_today(self), 'month')
    )
    date_to = fields.Date(
        string='Date To', 
        required=True, 
        default=lambda self: fields.Date.context_today(self)
    )
    
    # Field to display the final result (links or message)
    result_message = fields.Html(
        string="Download Links / Status",
        readonly=True
    )
    
    # State to control which view the wizard shows (input or result)
    state = fields.Selection([
        ('input', 'Date Input'),
        ('result', 'Result Display')
    ], default='input', required=True)

    @api.constrains('date_from', 'date_to')
    def _check_dates(self):
        for rec in self:
            if rec.date_from and rec.date_to and rec.date_from > rec.date_to:
                raise UserError(_('The "Date From" cannot be later than the "Date To".'))

    def action_confirm_export_pnd(self):
        """
        Action for the 'Submit' button: mocks CSV, calls external API, and updates the wizard state.
        """
        self.ensure_one()

        # --- MOCKING CSV DATA (Mock code from your original file adapted) ---
        csv_file = io.StringIO()
        writer = csv.writer(csv_file)
        writer.writerow([
            'No.', 'Tax ID', 'Title', 'Contact Name', 'Street', 'Street2', 'City', 'State', 'Zip',
            'Branch Number', 'Invoice/Bill Date', 'Tax Rate', 'Total Amount', 'WHT Amount',
            'WHT Condition', 'Tax Type'
        ])
        
        # Mock Data Generation based on date range context
        # In a real module, you would retrieve data here using self.date_from and self.date_to
        
        # Example Mock Row (adjust as needed for API expectation)
        # writer.writerow([
        #     1, '1234567890123', 'Mr.', 'John Doe', '123 Main St', '', 'Bangkok', 'BKK', '10110',
        #     '00000', datetime.now().strftime('%Y-%m-%d'), 3.0, 10000.00, 300.00,
        #     '3%', 'PND'
        # ])
        csv_content = """No.,Tax ID,Title,Contact Name,Street,Street2,City,State,Zip,Branch Number,Invoice/Bill Date,Tax Rate,Total Amount,WHT Amount,WHT Condition,Tax Type
        1,0103561015785,บริษัท,ห้างหุ้นส่วนจำกัด เค.จี.งานศิลป์,30/16 ตรอกหมู่บ้านฝนทองนิเวศน์ (ซอย 2) แขวงอนุสาวรีย์ เขตบางเขน กรุงเทพมหานคร 10220,,,,,,02/09/2025,3.00,6000.00,180.00,1,Service
        2,0105564011723,บริษัท,บริษัท วงศ์ธาดา จำกัด,88/217 ถนนเลียบคลองสอง เเขวงบางชัน เขตคลองสามวา กรุงเทพมหานคร 10510,,,,,,15/09/2025,3.00,3000.00,90.00,1,Service
        3,0101122334455,บริษัท,บริษัท ตัวอย่าง จำกัด,123/45 ถนนสุขุมวิท แขวงคลองตัน เขตคลองเตย กรุงเทพมหานคร 10110,,,,,,20/09/2025,3.00,4500.00,135.00,1,Service"""
        # csv_content = csv_file.getvalue()
        
        _logger.info(f"Content PND {csv_content}")
        # --- API Call (Using URL from your original request) ---
        url = "https://odoo.h3creation.com/api/v1/account/pnd53/print"
        files = {"file": ("pnd_data.csv", csv_content.encode('utf-8'), "text/csv")}
        link_text = ""
        
        try:
            response = requests.post(url, files=files, timeout=60)
            response.raise_for_status()
            data = response.json()
            paths = data.get('paths', [])
        
            if not paths:
                link_text = _("The API call succeeded, but no files were returned.")
            else:
                base_url = "https://odoo.h3creation.com"
                link_text = "<p><strong>Download successful! Click the links below:</strong></p>" + \
                            "<br/>".join([
                                f'<a href="{base_url}{p}" target="_blank">{p.split("/")[-1]}</a>' 
                                for p in paths
                            ])
        
        except requests.exceptions.RequestException as e:
            status = response.status_code if 'response' in locals() else 'N/A'
            _logger.error("PND API Error: Status %s, Detail: %s", status, str(e))
            link_text = f"<p style='color: red;'><strong>Export Failed (API Error):</strong></p> <p>{str(e)}</p> <p>Please check the external service status.</p>"
        except Exception as e:
            _logger.error("PND Internal Error: %s", str(e))
            link_text = f"<p style='color: red;'><strong>Internal Error:</strong></p> <p>{str(e)}</p>"


        # Update the current wizard record to display results and change state
        self.write({
            'result_message': link_text,
            'state': 'result'
        })
        
        """Fill Thai RD official PDF template"""

        template_path = get_module_resource(
            'account_pnd_report_th', 'static/pdf/thailand_withholding_tax.pdf'
        )
        # template_path = (
        #     self.env['ir.config_parameter']
        #     .sudo()
        #     .get_param('addons_path') +
        #     '/account_pnd_report/static/pdf/thailand_withholding_tax.pdf'
        # )

        reader = PdfReader(template_path)
        # Return a window action to refresh the current wizard form view
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'views': [(False, 'form')],
            'res_id': self.id,
            'target': 'new',
            'context': self.env.context,
        }
    
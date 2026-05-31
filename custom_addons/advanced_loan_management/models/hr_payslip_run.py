# -*- coding: utf-8 -*-
from odoo import models
import logging

_logger = logging.getLogger(__name__)


class HrPayslipRun(models.Model):
    _inherit = 'hr.payslip.run'

    def generate_payslips(self, *args, **kwargs):
        """Keep default payroll behaviour, but include all work-entry employees.

        The Work Entries calendar calls this method with explicit ``employee_ids``
        (every employee visible on the calendar). Enterprise ``generate_payslips``
        still filters by pay schedule (e.g. month), so daily workers are dropped.
        """
        employee_ids = kwargs.get('employee_ids')
        res = super().generate_payslips(*args, **kwargs)
        if employee_ids:
            self._add_missing_work_entry_payslips(employee_ids)
        return res

    def _add_missing_work_entry_payslips(self, employee_ids):
        Payslip = self.env['hr.payslip']
        for pay_run in self:
            existing_employee_ids = set(pay_run.slip_ids.mapped('employee_id').ids)
            missing_ids = [
                employee_id for employee_id in employee_ids
                if employee_id not in existing_employee_ids
            ]
            if not missing_ids:
                continue

            payslips_vals = []
            for employee in self.env['hr.employee'].browse(missing_ids):
                vals = pay_run._prepare_payslip_vals_from_employee(employee)
                if vals:
                    payslips_vals.append(vals)

            if not payslips_vals:
                continue

            _logger.info(
                "Pay run %s: adding %s payslip(s) for employees skipped by pay schedule filter (%s)",
                pay_run.display_name,
                len(payslips_vals),
                missing_ids,
            )
            new_slips = Payslip.with_context(tracking_disable=True).create(payslips_vals)
            pay_run.slip_ids |= new_slips

    def _prepare_payslip_vals_from_employee(self, employee):
        self.ensure_one()
        Payslip = self.env['hr.payslip']

        struct_id = False
        if 'struct_id' in self._fields and self.struct_id:
            struct_id = self.struct_id.id

        if hasattr(Payslip, 'get_payslip_vals'):
            slip_data = Payslip.get_payslip_vals(
                self.date_start,
                self.date_to,
                employee_id=employee.id,
                struct_id=[struct_id] if struct_id else False,
            )
            value = slip_data.get('value', {})
            if not value.get('struct_id'):
                _logger.warning(
                    "Skipping payslip for employee %s (%s): no contract/structure for %s - %s",
                    employee.display_name,
                    employee.id,
                    self.date_start,
                    self.date_end,
                )
                return False

            vals = {
                'employee_id': employee.id,
                'name': value.get('name') or employee.display_name,
                'struct_id': value['struct_id'],
                'payslip_run_id': self.id,
                'date_from': self.date_start,
                'date_to': self.date_end,
                'company_id': employee.company_id.id or self.company_id.id,
            }
            contract_id = value.get('contract_id')
            if contract_id:
                if 'version_id' in Payslip._fields:
                    vals['version_id'] = contract_id
                elif 'contract_id' in Payslip._fields:
                    vals['contract_id'] = contract_id

            for field_name in ('input_line_ids', 'worked_days_line_ids'):
                commands = [
                    (0, 0, line_vals)
                    for line_vals in value.get(field_name, [])
                    if isinstance(line_vals, dict)
                ]
                if commands:
                    vals[field_name] = commands

            if 'credit_note' in self._fields and self.credit_note:
                vals['credit_note'] = True
            return vals

        _logger.warning(
            "Cannot create missing payslip for employee %s: hr.payslip.get_payslip_vals unavailable",
            employee.id,
        )
        return False

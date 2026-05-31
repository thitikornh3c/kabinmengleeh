# -*- coding: utf-8 -*-
from odoo import models
import logging

_logger = logging.getLogger(__name__)


class HrPayslipRun(models.Model):
    _inherit = 'hr.payslip.run'

    def generate_payslips(self, *args, **kwargs):
        """Include every work-entry employee, not only the monthly schedule.

        The Work Entries calendar passes ``employee_ids`` for all visible
        employees, but Enterprise ``generate_payslips`` filters them by pay
        schedule (default month).  Resolve ``hr.version`` for each employee and
        call the same ``version_ids`` path used by the Pay Run wizard instead.
        """
        employee_ids = kwargs.get('employee_ids')
        if employee_ids:
            kwargs = dict(kwargs)
            kwargs.pop('employee_ids', None)
            version_ids = self._get_version_ids_for_work_entry_employees(employee_ids)
            if not version_ids:
                _logger.warning(
                    "Pay run %s: no contracts found for work entry employees %s",
                    self.ids,
                    employee_ids,
                )
                return super().generate_payslips(*args, **kwargs)
            kwargs['version_ids'] = version_ids
            _logger.info(
                "Pay run %s: generating payslips for %s version(s) from %s work entry employee(s)",
                self.ids,
                len(version_ids),
                len(employee_ids),
            )
        return super().generate_payslips(*args, **kwargs)

    def _get_version_ids_for_work_entry_employees(self, employee_ids):
        version_ids = []
        for pay_run in self:
            for employee in self.env['hr.employee'].browse(employee_ids):
                version = pay_run._get_employee_version(employee)
                if version:
                    version_ids.append(version.id)
                else:
                    _logger.warning(
                        "Pay run %s: no contract for employee %s (%s) in %s - %s",
                        pay_run.display_name,
                        employee.display_name,
                        employee.id,
                        pay_run.date_start,
                        pay_run.date_end,
                    )
        return version_ids

    def _get_employee_version(self, employee):
        self.ensure_one()
        contracts_by_emp = employee._get_contracts(
            date_start=self.date_start,
            date_end=self.date_end,
        )
        versions = contracts_by_emp.get(employee.id, self.env['hr.version'])
        if versions:
            return versions[0]
        if 'hr.version' in self.env:
            return self.env['hr.version'].search([
                ('employee_id', '=', employee.id),
                ('is_in_contract', '=', True),
            ], limit=1)
        return self.env['hr.version']

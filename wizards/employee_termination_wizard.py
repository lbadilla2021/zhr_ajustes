from datetime import date

from odoo import fields, models


class HrEmployeeTerminationWizard(models.TransientModel):
    _name = 'hr.employee.termination.wizard'
    _description = 'Dar de Baja Empleado'

    employee_id = fields.Many2one(
        'hr.employee',
        string='Empleado',
        required=True,
    )
    departure_reason_id = fields.Many2one(
        'hr.departure.reason',
        string='Motivo de Salida',
        required=True,
    )
    departure_date = fields.Date(
        string='Fecha de salida',
        required=True,
        default=lambda self: self._default_departure_date(),
    )

    def _default_departure_date(self):
        employee_id = self.env.context.get('default_employee_id')
        employee = (
            self.env['hr.employee'].with_context(active_test=False).browse(employee_id)
            if employee_id
            else self.env['hr.employee']
        )
        contracts = employee.contract_ids.filtered(
            lambda contract: contract.state == 'open'
        ).sorted(
            key=lambda contract: (contract.date_start or date.min, contract.id),
            reverse=True,
        )
        for contract in contracts:
            departure_date = contract.fecha_finiquito or contract.date_end
            if departure_date:
                return departure_date
        return fields.Date.context_today(self)

    def action_confirm(self):
        self.ensure_one()
        employee = self.employee_id.with_context(active_test=False)
        contracts = employee.contract_ids.filtered(
            lambda contract: contract.state in ('draft', 'open', 'close', 'expired')
        )
        all_contracts = employee.contract_ids.sudo().sorted(
            key=lambda contract: (contract.date_start or date.min, contract.id)
        )
        source_contracts = contracts.sudo().sorted(
            key=lambda contract: (contract.date_start or date.min, contract.id)
        ) or all_contracts
        last_contract = source_contracts[-1:] if source_contracts else self.env['hr.contract']
        for contract in contracts.sudo():
            vals = {
                'state': 'cancel',
                'fecha_finiquito': self.departure_date,
                'departure_reason_id': self.departure_reason_id.id,
            }
            if not contract.date_start or contract.date_start <= self.departure_date:
                vals['date_end'] = self.departure_date
            elif not contract.date_end:
                vals['date_end'] = contract.date_start
            contract.write(vals)

        if last_contract:
            reference = self.env.ref(
                'zhr_ajustes.hr_contract_reference_settlement',
                raise_if_not_found=False,
            )
            preserved_contract_date = (
                last_contract._get_preserved_contract_date(employee.id)
                or last_contract.fecha_contrato
                or employee.fecha_contrato
                or last_contract.date_start
                or self.departure_date
            )
            last_contract.copy({
                'reference_id': reference.id if reference else False,
                'name': employee.name and 'Finiquito - %s' % employee.name or 'Finiquito',
                'date_start': self.departure_date,
                'date_end': self.departure_date,
                'fecha_contrato': preserved_contract_date,
                'fecha_finiquito': self.departure_date,
                'departure_reason_id': self.departure_reason_id.id,
                'state': 'cancel',
                'kanban_state': 'normal',
            })

        employee.write({
            'active': False,
            'state': 'inactive',
            'departure_reason_id': self.departure_reason_id.id,
            'departure_date': self.departure_date,
            'fecha_finiquito': self.departure_date,
        })
        return {'type': 'ir.actions.act_window_close'}

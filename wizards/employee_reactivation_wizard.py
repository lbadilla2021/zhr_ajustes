from odoo import fields, models


class HrEmployeeReactivationWizard(models.TransientModel):
    _name = 'hr.employee.reactivation.wizard'
    _description = 'Dar de Alta Empleado'

    employee_id = fields.Many2one(
        'hr.employee',
        string='Empleado',
        required=True,
        readonly=True,
    )
    fecha_contrato = fields.Date(
        string='Fecha Contrato',
        required=True,
        default=fields.Date.context_today,
    )

    def action_confirm(self):
        self.ensure_one()
        employee = self.employee_id.with_context(active_test=False)
        all_contracts = employee.contract_ids.sudo().sorted(
            key=lambda contract: (contract.date_start or fields.Date.to_date('0001-01-01'), contract.id)
        )
        last_contract = all_contracts[-1:] if all_contracts else self.env['hr.contract']
        pending_contracts = employee.contract_ids.sudo().filtered(
            lambda contract: contract.state in ('draft', 'open', 'close', 'expired')
        )
        if pending_contracts:
            pending_contracts.write({'state': 'cancel'})

        if last_contract:
            reference = self.env.ref(
                'zhr_ajustes.hr_contract_reference_contract',
                raise_if_not_found=False,
            )
            last_contract.with_context(skip_preserve_contract_date=True).copy({
                'reference_id': reference.id if reference else False,
                'name': employee.name and 'Contrato - %s' % employee.name or 'Contrato',
                'fecha_contrato': self.fecha_contrato,
                'date_start': self.fecha_contrato,
                'date_end': False,
                'fecha_finiquito': False,
                'departure_reason_id': False,
                'state': 'draft',
                'kanban_state': 'normal',
            })

        employee.write({
            'active': True,
            'state': 'active',
            'fecha_contrato': self.fecha_contrato,
            'fecha_finiquito': False,
        })
        return {'type': 'ir.actions.act_window_close'}

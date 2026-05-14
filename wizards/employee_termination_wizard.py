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
    date_end = fields.Date(
        string='Fecha de Término',
        required=True,
        default=fields.Date.context_today,
    )

    def action_confirm(self):
        self.ensure_one()
        self.employee_id.write({
            'state': 'inactive',
            'departure_reason_id': self.departure_reason_id.id,
            'departure_date': self.date_end,
        })
        self.employee_id._update_contracts_on_termination(self.date_end)
        return {'type': 'ir.actions.act_window_close'}

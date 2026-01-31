from odoo import fields, models


class HrEmployeeReactivationWizard(models.TransientModel):
    _name = 'hr.employee.reactivation.wizard'
    _description = 'Dar de Alta Empleado'

    employee_id = fields.Many2one(
        'hr.employee',
        string='Empleado',
        required=True,
    )
    fecha_ingreso = fields.Date(string='Fecha de Ingreso', required=True)
    fecha_salida = fields.Date(string='Fecha de Salida')

    def action_confirm(self):
        self.ensure_one()
        self.employee_id.write({
            'state': 'active',
            'fecha_ingreso': self.fecha_ingreso,
            'fecha_salida': self.fecha_salida,
        })
        return {'type': 'ir.actions.act_window_close'}

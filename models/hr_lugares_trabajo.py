from odoo import fields, models


class HrTrabajos(models.Model):
    _name = 'hr.lugar.trabajo'
    _description = 'Lugares de Trabajo'

    name = fields.Char(string='Nombre', required=True)
    description = fields.Text(string='Descripcion')
    active = fields.Boolean(default=True)


class HrEmpleadoTrabajos(models.Model):
    _name = 'hr.employee.lugar.trabajo'
    _description = 'Lugares de trabajo por Contrato'

    contract_id = fields.Many2one(
        'hr.contract',
        string='Contrato',
        required=True,
        ondelete='cascade',
    )
    employee_id = fields.Many2one(
        'hr.employee',
        related='contract_id.employee_id',
        string='Empleado',
        store=True,
        readonly=True,
    )
    lugar_trabajo_id = fields.Many2one(
        'hr.lugar.trabajo',
        string='Lugar de trabajo',
        required=True,
    )
    amount = fields.Float(string='Valor')

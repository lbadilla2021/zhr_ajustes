from odoo import fields, models


class HrAssignedResource(models.Model):
    _name = 'hr.assigned.resource'
    _description = 'Recurso Asignado'

    name = fields.Char(string='Nombre', required=True)
    active = fields.Boolean(default=True)


class HrEmployeeAssignedResource(models.Model):
    _name = 'hr.employee.assigned.resource'
    _description = 'Recurso Asignado a Empleado'
    _rec_name = 'assigned_resource_id'
    _order = 'assignment_date desc, id desc'

    employee_id = fields.Many2one(
        'hr.employee',
        string='Empleado',
        required=True,
        ondelete='cascade',
    )
    assigned_resource_id = fields.Many2one(
        'hr.assigned.resource',
        string='Nombre del Recurso',
        required=True,
    )
    identification = fields.Char(string='Identificación')
    assignment_date = fields.Date(string='Fecha de Asignación')
    return_date = fields.Date(string='Fecha de Devolución')

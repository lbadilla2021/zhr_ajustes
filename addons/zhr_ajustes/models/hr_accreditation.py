from odoo import fields, models


class HrAccreditationType(models.Model):
    _name = 'hr.accreditation.type'
    _description = 'Tipo de Acreditación'

    name = fields.Char(string='Nombre', required=True)
    active = fields.Boolean(default=True)


class HrEmployeeAccreditation(models.Model):
    _name = 'hr.employee.accreditation'
    _description = 'Acreditación de Empleado'
    _rec_name = 'accreditation_type_id'
    _order = 'date_start desc, id desc'

    employee_id = fields.Many2one(
        'hr.employee',
        string='Empleado',
        required=True,
        ondelete='cascade',
    )
    accreditation_type_id = fields.Many2one(
        'hr.accreditation.type',
        string='Tipo de Acreditación',
        required=True,
    )
    date_start = fields.Date(string='Fecha Inicio')
    date_end = fields.Date(string='Fecha Término')
    active = fields.Boolean(default=True)
    attachment_id = fields.Many2one(
        'ir.attachment',
        string='Adjunto',
    )

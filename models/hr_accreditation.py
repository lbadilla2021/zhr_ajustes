from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class HrAccreditationType(models.Model):
    _name = 'hr.accreditation.type'
    _description = 'Tipo de Acreditación'

    name = fields.Char(string='Nombre', required=True)
    subtype_ids = fields.One2many(
        'hr.accreditation.subtype',
        'accreditation_type_id',
        string='Tipos',
    )
    active = fields.Boolean(default=True)


class HrAccreditationSubtype(models.Model):
    _name = 'hr.accreditation.subtype'
    _description = 'Tipo de una Acreditación'
    _order = 'accreditation_type_id, sequence, name, id'
    _rec_names_search = ['name', 'description']

    name = fields.Char(string='Tipo', required=True)
    description = fields.Char(
        string='Descripción',
        help='Breve descripción que permite identificar de qué trata este tipo.',
    )
    accreditation_type_id = fields.Many2one(
        'hr.accreditation.type',
        string='Tipo de Acreditación',
        required=True,
        ondelete='cascade',
        index=True,
    )
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)

    _sql_constraints = [
        (
            'name_accreditation_type_unique',
            'unique(name, accreditation_type_id)',
            'El tipo ya existe para esta acreditación.',
        ),
    ]


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
    accreditation_subtype_ids = fields.Many2many(
        'hr.accreditation.subtype',
        'hr_employee_accreditation_subtype_rel',
        'employee_accreditation_id',
        'accreditation_subtype_id',
        string='Tipo',
        domain=(
            "[('accreditation_type_id', '=', accreditation_type_id), "
            "('active', '=', True)]"
        ),
    )
    date_start = fields.Date(string='Fecha Inicio')
    date_end = fields.Date(string='Fecha Término')
    active = fields.Boolean(default=True)
    attachment_id = fields.Many2one(
        'ir.attachment',
        string='Adjunto',
    )

    @api.onchange('accreditation_type_id')
    def _onchange_accreditation_type_id(self):
        for accreditation in self:
            accreditation.accreditation_subtype_ids = (
                accreditation.accreditation_subtype_ids.filtered(
                    lambda subtype: (
                        subtype.accreditation_type_id
                        == accreditation.accreditation_type_id
                    )
                )
            )

    @api.constrains('accreditation_type_id', 'accreditation_subtype_ids')
    def _check_accreditation_subtypes(self):
        for accreditation in self:
            invalid_subtypes = accreditation.accreditation_subtype_ids.filtered(
                lambda subtype: (
                    subtype.accreditation_type_id
                    != accreditation.accreditation_type_id
                )
            )
            if invalid_subtypes:
                raise ValidationError(_(
                    'Los tipos seleccionados deben pertenecer al Tipo de '
                    'Acreditación elegido.'
                ))

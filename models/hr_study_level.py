from odoo import api, fields, models


class HrStudyLevel(models.Model):
    _name = 'hr.study.level'
    _description = 'Nivel de estudio'
    _order = 'name, code'

    name = fields.Char(string='Nivel de estudio', required=True)
    code = fields.Char(string='Código', required=True)
    active = fields.Boolean(string='Activo', default=True)

    _sql_constraints = [
        (
            'hr_study_level_name_unique',
            'unique(name)',
            'El nivel de estudio ya existe.',
        ),
        (
            'hr_study_level_code_unique',
            'unique(code)',
            'El código del nivel de estudio ya existe.',
        ),
    ]

    @api.depends('name', 'code')
    def _compute_display_name(self):
        for level in self:
            level.display_name = (
                f'{level.name} ({level.code})' if level.code else level.name
            )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('code'):
                vals['code'] = vals['code'].strip().upper()
            if vals.get('name'):
                vals['name'] = vals['name'].strip()
        return super().create(vals_list)

    def write(self, vals):
        vals = dict(vals)
        if vals.get('code'):
            vals['code'] = vals['code'].strip().upper()
        if vals.get('name'):
            vals['name'] = vals['name'].strip()
        return super().write(vals)

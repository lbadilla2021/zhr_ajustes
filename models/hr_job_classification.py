from odoo import api, fields, models


class HrJobSenceClassification(models.Model):
    _name = 'hr.job.sence.classification'
    _description = 'Clasificación Sence'
    _order = 'code, name'

    code = fields.Char(string='Código', required=True)
    name = fields.Char(string='Nombre', required=True)
    active = fields.Boolean(string='Activo', default=True)

    _sql_constraints = [
        (
            'hr_job_sence_classification_code_unique',
            'unique(code)',
            'El código de la clasificación Sence ya existe.',
        ),
        (
            'hr_job_sence_classification_name_unique',
            'unique(name)',
            'El nombre de la clasificación Sence ya existe.',
        ),
    ]

    @api.depends('name', 'code')
    def _compute_display_name(self):
        for classification in self:
            classification.display_name = (
                f'{classification.name} ({classification.code})'
                if classification.code
                else classification.name
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


class HrJobIneClassification(models.Model):
    _name = 'hr.job.ine.classification'
    _description = 'Clasificación INE'
    _order = 'code, name'

    code = fields.Char(string='Código', required=True)
    name = fields.Char(string='Nombre', required=True)
    active = fields.Boolean(string='Activo', default=True)

    _sql_constraints = [
        (
            'hr_job_ine_classification_code_unique',
            'unique(code)',
            'El código de la clasificación INE ya existe.',
        ),
        (
            'hr_job_ine_classification_name_unique',
            'unique(name)',
            'El nombre de la clasificación INE ya existe.',
        ),
    ]

    @api.depends('name', 'code')
    def _compute_display_name(self):
        for classification in self:
            classification.display_name = (
                f'{classification.name} ({classification.code})'
                if classification.code
                else classification.name
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


class HrJob(models.Model):
    _inherit = 'hr.job'

    sence_classification_id = fields.Many2one(
        'hr.job.sence.classification',
        string='Sence',
        ondelete='restrict',
    )
    ine_classification_id = fields.Many2one(
        'hr.job.ine.classification',
        string='INE',
        ondelete='restrict',
    )

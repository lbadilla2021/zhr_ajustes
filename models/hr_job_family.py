from odoo import fields, models


class HrJobFamily(models.Model):
    _name = 'hr.job.family'
    _description = 'Familias de Cargos'
    _order = 'name'

    name = fields.Char(string='Nombre', required=True)
    code = fields.Char(string='Codigo')
    description = fields.Text(string='Descripcion')
    active = fields.Boolean(default=True)


class HrJob(models.Model):
    _inherit = 'hr.job'

    job_family_id = fields.Many2one(
        'hr.job.family',
        string='Familia',
        ondelete='restrict',
    )
    job_creation_date = fields.Date(
        string='Fecha',
        default=fields.Date.context_today,
    )

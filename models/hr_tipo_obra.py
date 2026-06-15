from odoo import fields, models


class HrTipoObra(models.Model):
    _name = 'hr.tipo.obra'
    _description = 'Tipos de Obra'

    name = fields.Char(string='Nombre', required=True)
    active = fields.Boolean(default=True)

class HrDuracionObra(models.Model):
    _name = 'hr.duracion.obra'
    _description = 'Duración de las Obras'

    name = fields.Char(string='Duración', required=True)
    active = fields.Boolean(default=True)
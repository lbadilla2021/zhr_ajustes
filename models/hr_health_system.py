from odoo import fields, models


class HrHealthSystem(models.Model):
    _name = 'hr.health_system'
    _description = 'Sistema de Salud'

    name = fields.Char(string='Nombre', required=True)
    type = fields.Selection(
        [('isapre', 'Isapre'), ('fonasa', 'Fonasa')],
        string='Tipo',
        required=True,
    )
    active = fields.Boolean(default=True)

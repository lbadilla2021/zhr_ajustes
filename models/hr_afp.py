from odoo import fields, models


class HrAfp(models.Model):
    _name = 'hr.afp'
    _description = 'AFP'

    name = fields.Char(string='Nombre', required=True)
    code = fields.Char(string='Código')
    active = fields.Boolean(default=True)

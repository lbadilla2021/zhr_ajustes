from odoo import fields, models


class HrCity(models.Model):
    _name = 'hr.city'
    _description = 'Ciudad'
    _order = 'name'

    name = fields.Char(string='Ciudad', required=True)
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ('name_unique', 'unique(name)', 'La ciudad ya existe.'),
    ]

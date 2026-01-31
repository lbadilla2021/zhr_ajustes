from odoo import fields, models


class HrSystemSchedule(models.Model):
    _name = 'hr.system.schedule'
    _description = 'Sistema Horario'

    name = fields.Char(string='Sistema Horario', required=True)
    active = fields.Boolean(default=True)

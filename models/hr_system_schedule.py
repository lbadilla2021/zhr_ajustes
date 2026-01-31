# -*- coding: utf-8 -*-
from odoo import fields, models


class HrSystemSchedule(models.Model):
    _name = 'hr.system.schedule'
    _description = 'Sistema Horario'

    name = fields.Char(string='Nombre', required=True)
    code = fields.Char(string='Código')
    active = fields.Boolean(default=True)

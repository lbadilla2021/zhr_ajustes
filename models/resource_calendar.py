from odoo import fields, models


class ResourceCalendar(models.Model):
    _inherit = 'resource.calendar'

    system_schedule = fields.Char(string='Sistema Horario')

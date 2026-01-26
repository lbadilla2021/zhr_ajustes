from odoo import fields, models


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    apellido_paterno = fields.Char(string='Apellido Paterno')
    apellido_materno = fields.Char(string='Apellido Materno')
    nombres = fields.Char(string='Nombres')
    nombre_preferido = fields.Char(string='Nombre Preferido')
    analytic_distribution = fields.Json(string='Centro de Costo')

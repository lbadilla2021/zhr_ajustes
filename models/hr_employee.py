from odoo import fields, models


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    apellido_paterno = fields.Char(string='Apellido Paterno')
    apellido_materno = fields.Char(string='Apellido Materno')
    nombres = fields.Char(string='Nombres')
    nombre_preferido = fields.Char(string='Nombre Preferido')
    analytic_account_id = fields.Many2one(
        'account.analytic.account',
        string='Centro de Costo',
        domain="[('plan_id.name', '=', 'Barca SpA')]",
        help='Seleccione el centro de costo dentro del plan analítico de la empresa.',
    )

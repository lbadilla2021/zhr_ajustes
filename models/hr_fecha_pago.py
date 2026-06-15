from odoo import api, fields, models
from odoo.exceptions import ValidationError


class HrFechaPago(models.Model):
    _name = 'zhr.fecha.pago'
    _description = 'Fecha de Pago de Remuneraciones'

    dia_pago = fields.Integer(string='Día de Pago', required=True, default=6)

    @api.constrains('dia_pago')
    def _check_dia_pago(self):
        for record in self:
            if not 1 <= record.dia_pago <= 31:
                raise ValidationError('El día de pago debe estar entre 1 y 31.')

from odoo import fields, models


class HrContractReference(models.Model):
    _name = 'hr.contract.reference'
    _description = 'Referencia de Contrato'
    _order = 'sequence, name'

    name = fields.Char(string='Referencia', required=True)
    reference_type = fields.Selection(
        [
            ('contract', 'Contrato'),
            ('annex', 'Anexo'),
        ],
        string='Tipo',
        required=True,
        default='annex',
    )
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)

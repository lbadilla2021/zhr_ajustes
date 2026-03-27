from odoo import fields, models


class HrContractOperadorWizard(models.TransientModel):
    _name = 'hr.contract.operador.wizard'
    _description = 'Seleccion de tipo de contrato operador'

    contract_id = fields.Many2one(
        'hr.contract',
        string='Contrato',
        required=True,
        readonly=True,
    )
    contract_type = fields.Selection(
        [
            ('plazo', 'Contrato por plazo'),
            ('faena', 'Contrato por faena'),
        ],
        string='Tipo de contrato',
        required=True,
        default='plazo',
    )
    faena_text = fields.Char(
        string='Texto de faena',
        help='Texto temporal que se insertara en SEPTIMO cuando el contrato sea por faena.',
    )

    def action_confirm(self):
        self.ensure_one()
        return self.env.ref('zhr_ajustes.action_report_contract_employee_operador').report_action(self)

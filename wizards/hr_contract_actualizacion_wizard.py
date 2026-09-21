from odoo import api, fields, models


class HrContractActualizacionWizard(models.TransientModel):
    _name = 'hr.contract.actualizacion.wizard'
    _description = 'Seleccion de anexo de contrato'

    contract_id = fields.Many2one(
        'hr.contract',
        string='Contrato',
        required=True,
        readonly=True,
    )
    report_type = fields.Selection(
        [
            ('actualizacion', 'Anexo Actualizacion'),
            ('modificacion', 'Anexo Modificacion'),
            ('renovacion', 'Anexo Renovacion'),
        ],
        string='Tipo de anexo',
        required=True,
        default='actualizacion',
    )
    show_sueldo_base = fields.Boolean(string='Sueldo base', default=True)
    show_cargo_actual = fields.Boolean(string='Cargo actual', default=True)
    show_jornada_trabajo = fields.Boolean(string='Jornada de trabajo', default=True)
    show_payment_concepts = fields.Boolean(
        string='Conceptos de pago',
        default=False,
    )

    @api.onchange('report_type')
    def _onchange_report_type(self):
        for wizard in self:
            show_options = wizard.report_type in (
                'actualizacion',
                'modificacion',
            )
            wizard.show_sueldo_base = show_options
            wizard.show_cargo_actual = show_options
            wizard.show_jornada_trabajo = show_options
            wizard.show_payment_concepts = (
                wizard.report_type == 'modificacion'
            )

    def action_confirm(self):
        self.ensure_one()
        report_xml_id = {
            'actualizacion': 'zhr_ajustes.action_report_actualizacion',
            'modificacion': 'zhr_ajustes.action_report_modificacion',
            'renovacion': 'zhr_ajustes.action_report_renovacion',
        }[self.report_type]
        return self.env.ref(report_xml_id).report_action(self)

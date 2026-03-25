from odoo import fields, models


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
            ('renovacion', 'Anexo Renovacion'),
        ],
        string='Tipo de anexo',
        required=True,
        default='actualizacion',
    )

    def action_confirm(self):
        self.ensure_one()
        report_xml_id = {
            'actualizacion': 'zhr_ajustes.action_report_actualizacion',
            'renovacion': 'zhr_ajustes.action_report_renovacion',
        }[self.report_type]
        return self.env.ref(report_xml_id).report_action(self.contract_id)

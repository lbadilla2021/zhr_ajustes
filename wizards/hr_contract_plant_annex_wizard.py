from odoo import fields, models


class HrContractPlantAnnexWizard(models.TransientModel):
    _name = 'hr.contract.plant.annex.wizard'
    _description = 'Seleccion de Cliente para Anexo Planta'

    contract_id = fields.Many2one(
        'hr.contract',
        string='Contrato',
        required=True,
        readonly=True,
    )
    client_id = fields.Many2one(
        'hr.plant.annex.client',
        string='Cliente',
        required=True,
    )

    def action_print(self):
        self.ensure_one()
        report = self.env.ref(
            'zhr_ajustes.action_report_anexo_planta'
        ).with_context(
            plant_annex_client_id=self.client_id.id,
        )
        return report.report_action(
            self.contract_id,
            config=False,
        )

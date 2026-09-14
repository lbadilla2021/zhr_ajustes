from odoo import fields, models
from odoo.exceptions import UserError


class HrPlantAnnexClient(models.Model):
    _name = 'hr.plant.annex.client'
    _description = 'Cliente de Anexo Planta'
    _order = 'name'

    name = fields.Char(string='Cliente', required=True)
    clause_html = fields.Html(
        string='Clausula',
        required=True,
        sanitize=True,
    )

    _sql_constraints = [
        (
            'hr_plant_annex_client_name_unique',
            'unique(name)',
            'Ya existe un cliente de Anexo Planta con este nombre.',
        ),
    ]


class ReportAnexoPlanta(models.AbstractModel):
    _name = 'report.zhr_ajustes.report_anexo_planta'
    _description = 'Reporte Anexo Planta'

    def _get_report_values(self, docids, data=None):
        report_data = data or {}
        document_ids = docids or report_data.get('ids') or self.env.context.get(
            'active_ids',
            [],
        )
        if isinstance(document_ids, int):
            document_ids = [document_ids]

        client_id = report_data.get(
            'plant_annex_client_id'
        ) or self.env.context.get('plant_annex_client_id')
        client = self.env['hr.plant.annex.client'].browse(client_id).exists()
        if not client:
            raise UserError('Debe seleccionar el cliente del Anexo Planta.')
        return {
            'doc_ids': document_ids,
            'doc_model': 'hr.contract',
            'docs': self.env['hr.contract'].browse(document_ids),
            'plant_annex_client': client,
        }

from odoo import fields, models


class HrEmployeeEmploymentCertificateWizard(models.TransientModel):
    _name = 'hr.employee.employment.certificate.wizard'
    _description = 'Emision de Certificado Laboral'

    employee_id = fields.Many2one(
        'hr.employee',
        string='Empleado',
        required=True,
        readonly=True,
    )
    presentation_place = fields.Char(
        string='Presentar en',
        required=True,
        help='Institucion o entidad donde se presentara el certificado.',
    )
    additional_clause = fields.Text(
        string='Clausula Adicional',
        help='Texto opcional que se agregara al certificado laboral.',
    )

    def action_print(self):
        self.ensure_one()
        report = self.env.ref(
            'zhr_ajustes.action_report_certificado_laboral'
        ).with_context(
            employment_certificate_presentation_place=self.presentation_place,
            employment_certificate_additional_clause=(
                self.additional_clause or ''
            ).strip(),
        )
        return report.report_action(self.employee_id, config=False)

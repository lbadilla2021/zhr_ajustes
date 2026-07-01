import io

from odoo import api, fields, models
from odoo.exceptions import UserError


class HrContractMassPrintWizard(models.TransientModel):
    _name = 'hr.contract.mass.print.wizard'
    _description = 'Impresion masiva de contratos'

    contract_ids = fields.Many2many(
        'hr.contract',
        string='Contratos seleccionados',
        required=True,
        readonly=True,
    )
    employee_ids = fields.Many2many(
        'hr.employee',
        string='Empleados seleccionados',
        compute='_compute_employee_ids',
    )
    show_actualizacion_options = fields.Boolean(default=False)
    actualizacion_report_type = fields.Selection(
        [
            ('actualizacion', 'Anexo Actualizacion'),
            ('renovacion', 'Anexo Renovacion'),
        ],
        string='Tipo de actualizacion',
        required=True,
        default='actualizacion',
    )
    show_sueldo_base = fields.Boolean(string='Sueldo base', default=True)
    show_cargo_actual = fields.Boolean(string='Cargo actual', default=True)
    show_jornada_trabajo = fields.Boolean(string='Jornada de trabajo', default=True)

    @api.onchange('actualizacion_report_type')
    def _onchange_actualizacion_report_type(self):
        for wizard in self:
            show_options = wizard.actualizacion_report_type == 'actualizacion'
            wizard.show_sueldo_base = show_options
            wizard.show_cargo_actual = show_options
            wizard.show_jornada_trabajo = show_options

    def action_print_contract(self):
        return self._generate_merged_pdf('contract')

    def action_print_anexo_planta(self):
        return self._generate_merged_pdf('anexo_planta')

    def action_print_pacto_he(self):
        return self._generate_merged_pdf('pacto_he')

    def action_print_actualizacion(self):
        self.ensure_one()
        self.show_actualizacion_options = True
        return {
            'type': 'ir.actions.act_window',
            'name': 'Impresion masiva de contratos',
            'res_model': self._name,
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
        }

    def action_confirm_actualizacion(self):
        return self._generate_merged_pdf('actualizacion')

    @api.depends('contract_ids', 'contract_ids.employee_id')
    def _compute_employee_ids(self):
        for wizard in self:
            wizard.employee_ids = wizard.contract_ids.mapped('employee_id')

    def _generate_merged_pdf(self, document_type):
        self.ensure_one()
        if not self.contract_ids:
            raise UserError('Debe seleccionar al menos un contrato.')

        report_model = self.env['ir.actions.report']
        streams = []
        for contract in self.contract_ids:
            report_xml_id, record = self._get_report_record(document_type, contract)
            pdf_content, _content_type = report_model._render_qweb_pdf(
                self.env.ref(report_xml_id),
                res_ids=record.ids,
            )
            streams.append(io.BytesIO(pdf_content))

        merged_stream = report_model._merge_pdfs(streams)
        attachment = self.env['ir.attachment'].create({
            'name': self._get_filename(document_type),
            'type': 'binary',
            'raw': merged_stream.getvalue(),
            'mimetype': 'application/pdf',
            'res_model': self._name,
            'res_id': self.id,
        })
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s?download=true' % attachment.id,
            'target': 'self',
        }

    def _get_report_record(self, document_type, contract):
        if document_type == 'contract':
            return self._get_contract_report_xml_id(contract), contract
        if document_type == 'anexo_planta':
            return 'zhr_ajustes.action_report_anexo_planta', contract
        if document_type == 'pacto_he':
            return 'zhr_ajustes.action_report_pacto_he', contract

        wizard = self.env['hr.contract.actualizacion.wizard'].create({
            'contract_id': contract.id,
            'report_type': self.actualizacion_report_type,
            'show_sueldo_base': self.show_sueldo_base,
            'show_cargo_actual': self.show_cargo_actual,
            'show_jornada_trabajo': self.show_jornada_trabajo,
        })
        report_xml_id = {
            'actualizacion': 'zhr_ajustes.action_report_actualizacion',
            'renovacion': 'zhr_ajustes.action_report_renovacion',
        }[self.actualizacion_report_type]
        return report_xml_id, wizard

    def _get_contract_report_xml_id(self, contract):
        structure_name = (contract.struct_id.name or '').strip().lower()
        if 'ejecutivo' in structure_name:
            return 'zhr_ajustes.action_report_contract_employee_ejecutivo'
        if 'profesional' in structure_name:
            return 'zhr_ajustes.action_report_contract_employee_profesional'
        return 'zhr_ajustes.action_report_contract_employee_operador'

    def _get_filename(self, document_type):
        labels = {
            'contract': 'Contratos',
            'anexo_planta': 'Anexos Planta',
            'pacto_he': 'Pactos HE',
            'actualizacion': 'Actualizaciones de Contrato',
        }
        return '%s.pdf' % labels[document_type]

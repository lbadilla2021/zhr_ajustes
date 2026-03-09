from odoo import fields, models
from babel.dates import format_date


class HrContract(models.Model):
    _inherit = 'hr.contract'

    employee_payment_concept_ids = fields.One2many(
        related='employee_id.payment_concept_line_ids',
        readonly=False,
        string='Conceptos de Pago',
    )

    def action_print_contract(self):
        self.ensure_one()

        # Obtener nombre de la estructura salarial
        structure_name = ''
        if self.struct_id:
            structure_name = (self.struct_id.name or '').strip().lower()

        # Selección del reporte según estructura
        if 'ejecutivo' in structure_name:
            report_xml_id = 'zhr_ajustes.action_report_contract_employee_ejecutivo'
        elif 'profesional' in structure_name:
            report_xml_id = 'zhr_ajustes.action_report_contract_employee_profesional'
        elif 'operativo' in structure_name:
            report_xml_id = 'zhr_ajustes.action_report_contract_employee_operador'
        else:
            report_xml_id = 'zhr_ajustes.action_report_contract_employee_operador'

        return self.env.ref(report_xml_id).report_action(self)

    # ✅ NUEVO MÉTODO
    def action_print_anexo_planta(self):
        self.ensure_one()

        return self.env.ref(
            'zhr_ajustes.action_report_anexo_planta'
        ).report_action(self)

    def action_print_pacto_he(self):
        self.ensure_one()
        return self.env.ref(
            'zhr_ajustes.action_report_pacto_he'
        ).report_action(self)

    def action_print_actualizacion(self):
        self.ensure_one()
        return self.env.ref(
            'zhr_ajustes.action_report_actualizacion'
        ).report_action(self)    

    def format_date_es(self, fecha):
        if fecha:
            return format_date(fecha, format="d 'de' MMMM 'de' yyyy", locale='es')
        return ''
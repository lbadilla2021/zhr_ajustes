from odoo import fields, models

class HrContract(models.Model):
    _inherit = 'hr.contract'


    employee_payment_concept_ids = fields.One2many(
        related='employee_id.payment_concept_line_ids',
        readonly=False,
        string='Conceptos de Pago',
    )

    def action_print_contract(self):
        self.ensure_one()

        structure_name = ''
        if 'structure_type_id' in self._fields and self.structure_type_id:
            structure_name = self.structure_type_id.name or ''
        elif 'structure_id' in self._fields and self.structure_id:
            structure_name = self.structure_id.name or ''

        report_by_structure = {
            'operador': 'zhr_ajustes.action_report_contract_employee_operador',
            'profesional': 'zhr_ajustes.action_report_contract_employee_profesional',
            'ejecutivo': 'zhr_ajustes.action_report_contract_employee_ejecutivo',
        }
        report_xml_id = report_by_structure.get(
            (structure_name or '').strip().lower(),
            'zhr_ajustes.action_report_contract_employee_operador',
        )
        return self.env.ref(report_xml_id).report_action(self)

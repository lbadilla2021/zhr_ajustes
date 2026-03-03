from odoo import fields, models

class HrContract(models.Model):
    _inherit = 'hr.contract'


    employee_payment_concept_ids = fields.One2many(
        related='employee_id.payment_concept_line_ids',
        readonly=False,
        string='Conceptos de Pago',
    )

    def action_print_contract(self):
        return self.env.ref(
            'zhr_ajustes.action_report_contract_employee'
        ).report_action(self)

from odoo import models

class HrContract(models.Model):
    _inherit = 'hr.contract'

    def action_print_contract(self):
        return self.env.ref(
            'zhr_ajustes.action_report_contract_employee'
        ).report_action(self)

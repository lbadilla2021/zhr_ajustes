from odoo import api, fields, models
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta


class HrContractDuplicateWizard(models.TransientModel):
    _name = 'hr.contract.duplicate.wizard'
    _description = 'Duplicar contrato'

    contract_id = fields.Many2one(
        'hr.contract',
        string='Contrato',
        required=True,
        readonly=True,
    )
    date_start = fields.Date(
        string='Nueva fecha de inicio',
        required=True,
        default=lambda self: self._default_date_start(),
    )
    reference_id = fields.Many2one(
        'hr.contract.reference',
        string='Referencia del contrato',
        required=True,
        domain=[('active', '=', True)],
        default=lambda self: self.env.ref(
            'zhr_ajustes.hr_contract_reference_contract',
            raise_if_not_found=False,
        ),
    )
    name = fields.Char(
        string='Referencia generada',
        compute='_compute_name',
        readonly=True,
    )

    def _default_date_start(self):
        contract_id = self.env.context.get('default_contract_id')
        if contract_id:
            contract = self.env['hr.contract'].browse(contract_id)
            previous_end = contract.date_end or contract.fecha_finiquito
            if previous_end:
                return previous_end + relativedelta(days=1)
        return fields.Date.context_today(self)

    @api.depends(
        'reference_id',
        'contract_id.employee_id.name',
    )
    def _compute_name(self):
        for wizard in self:
            wizard.name = wizard._build_reference_name()

    def _build_reference_name(self):
        self.ensure_one()
        employee_name = self.contract_id.employee_id.name or ''
        reference_name = self.reference_id.name or ''
        return ' - '.join(part for part in (reference_name, employee_name) if part)

    def action_confirm(self):
        self.ensure_one()
        if not self.reference_id:
            raise ValidationError('Debe seleccionar la referencia del contrato.')

        new_contract = self.contract_id.action_duplicate_with_new_reference(
            self.date_start,
            self._build_reference_name(),
            self.reference_id.id,
        )
        return {
            'type': 'ir.actions.act_window',
            'name': 'Contrato duplicado',
            'res_model': 'hr.contract',
            'view_mode': 'form',
            'res_id': new_contract.id,
            'target': 'current',
        }

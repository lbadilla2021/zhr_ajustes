from odoo import fields, models


class HrPaymentConcept(models.Model):
    _name = 'hr.payment.concept'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Conceptos de Pago'

    name = fields.Char(string='Nombre', required=True)
    description = fields.Text(string='Descripcion')
    target_group = fields.Char(string='Grupo Objetivo')
    value_text = fields.Char(string='Valor')
    modification_date = fields.Date(
        string='Fecha modificación',
        tracking=True,
    )
    active = fields.Boolean(default=True)


class HrEmployeePaymentConcept(models.Model):
    _name = 'hr.employee.payment.concept'
    _description = 'Conceptos de pago por Empleado'

    contract_id = fields.Many2one(
        'hr.contract',
        string='Contrato',
        ondelete='cascade',
    )
    employee_id = fields.Many2one(
        'hr.employee',
        related='contract_id.employee_id',
        string='Empleado',
        store=True,
        readonly=True,
    )

    payment_concept_id = fields.Many2one(
        'hr.payment.concept',
        string='Conceptos de Pago',
        required=True,
    )

    amount = fields.Float(string='Valor', required=True)

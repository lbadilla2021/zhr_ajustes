from odoo import fields, models


class HrPaymentConcept(models.Model):
    _name = 'hr.payment.concept'
    _description = 'Concepto de Pago'

    name = fields.Char(string='Nombre', required=True)
    active = fields.Boolean(default=True)


class HrEmployeePaymentConcept(models.Model):
    _name = 'hr.employee.payment.concept'
    _description = 'Asignación de Concepto de Pago por Trabajador'

    employee_id = fields.Many2one(
        'hr.employee',
        string='Empleado',
        required=True,
        ondelete='cascade',
    )
    payment_concept_id = fields.Many2one(
        'hr.payment.concept',
        string='Concepto',
        required=True,
    )
    amount = fields.Float(string='Valor', required=True)

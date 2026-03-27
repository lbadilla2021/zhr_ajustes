from odoo import fields, models, api
from babel.dates import format_date

class HrContract(models.Model):
    _inherit = 'hr.contract'

    schedule_pay = fields.Selection(
        selection_add=[('daily', 'Diario')],
        ondelete={'daily': 'set default'},
    )

    wage_text = fields.Char(compute="_compute_wage_text")

    @api.depends('schedule_pay')
    def _compute_schedule_pay_name(self):
        schedule_pay_labels = {
            'daily': 'diario',
            'weekly': 'semanal',
            'bi-weekly': 'quincenal',
            'bi-monthly': 'bimensual',
            'monthly': 'mensual',
            'quarterly': 'trimestral',
            'semi-annually': 'semestral',
            'annually': 'anual',
        }

        for rec in self:
            rec.schedule_pay_name = schedule_pay_labels.get(
                rec.schedule_pay,
                rec.schedule_pay or '',
            )

    @api.depends('wage')
    def _compute_wage_text(self):
        for rec in self:
            if rec.wage:
                text = rec.company_id.currency_id.amount_to_text(rec.wage)
                rec.wage_text = text.capitalize()
            else:
                rec.wage_text = ""    

    employee_payment_concept_ids = fields.One2many(
        'hr.employee.payment.concept',
        'contract_id',
        string='Conceptos de Pago',
    )

    tipo_obra_id = fields.Many2one(
        'hr.tipo.obra',
        string='Tipo de obra',
    )

    duracion_obra = fields.Char(
        string='Duración de obra',
    )
    
    lugar_trabajo_id = fields.Many2one(
        'hr.lugar.trabajo',
        string='Lugar de trabajo',
    )
    is_por_obra = fields.Boolean(
        compute='_compute_is_por_obra',
    )

    lugar_trabajo_line_ids = fields.One2many(
        'hr.employee.lugar.trabajo',
        'contract_id',
        string='Lugares de trabajo',
    )

    @api.depends('contract_type_id')
    def _compute_is_por_obra(self):
        for rec in self:
            contract_type_name = (rec.contract_type_id.name or '').strip().lower()
            rec.is_por_obra = 'obra' in contract_type_name

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

    schedule_details = fields.Char(
        compute="_compute_schedule_details"
    )

    def _compute_schedule_details(self):
        
        for rec in self:
            if rec.resource_calendar_id and rec.resource_calendar_id.attendance_ids:
                att = rec.resource_calendar_id.attendance_ids[0]
                rec.schedule_details = rec.resource_calendar_id.system_schedule
            else:
                rec.schedule_details = ""
    
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
        return {
            'type': 'ir.actions.act_window',
            'name': 'Seleccionar anexo',
            'res_model': 'hr.contract.actualizacion.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_contract_id': self.id,
            },
        }

    def format_date_es(self, fecha):
        if fecha:
            return format_date(fecha, format="d 'de' MMMM 'de' yyyy", locale='es')
        return ''

    def format_today_es(self):
        self.ensure_one()
        return self.format_date_es(fields.Date.context_today(self))

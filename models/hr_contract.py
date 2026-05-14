from babel.dates import format_date
from markupsafe import Markup, escape

from odoo import api, fields, models


class HrContract(models.Model):
    _inherit = 'hr.contract'

    state = fields.Selection([
        ('draft', 'New'),
        ('open', 'Vigente'),
        ('close', 'Vencido'),
        ('cancel', 'Terminado'),
    ], string='Status', group_expand=True, copy=False,
        tracking=True, help='Status of the contract', default='draft')

    employee_identification_id = fields.Char(
        string='N° Identificación Empleado',
        related='employee_id.identification_id',
        store=True,
        readonly=True,
        index=True,
        help='Número de identificación del empleado asociado al contrato.',
    )

    @api.model
    def _update_contract_state_labels(self):
        labels = {
            'open': 'Vigente',
            'close': 'Vencido',
            'cancel': 'Terminado',
        }
        field = self.env['ir.model.fields'].sudo().search([
            ('model', '=', 'hr.contract'),
            ('name', '=', 'state'),
        ], limit=1)
        for value, label in labels.items():
            self.env.cr.execute(
                """
                UPDATE ir_model_fields_selection
                   SET name = jsonb_set(
                       jsonb_set(COALESCE(name, '{}'::jsonb), '{es_CL}', to_jsonb(%s::text), true),
                       '{es_419}', to_jsonb(%s::text), true
                   )
                 WHERE field_id = %s
                   AND value = %s
                """,
                (label, label, field.id, value),
            )
        self.env['ir.model.fields.selection'].invalidate_model(['name'])
        return True

    schedule_pay = fields.Selection(
        selection_add=[('daily', 'Diario')],
        ondelete={'daily': 'set default'},
    )

    wage_text = fields.Char(compute="_compute_wage_text")

    @api.model_create_multi
    def create(self, vals_list):
        contracts = super().create(vals_list)
        contracts._send_contract_update_notification()
        return contracts

    def write(self, vals):
        res = super().write(vals)
        if {'employee_id', 'date_start', 'date_end', 'state'} & set(vals):
            self._send_contract_update_notification()
        return res

    @api.model
    def _cron_update_expired_contracts(self):
        """Close or cancel open contracts whose end date is already expired."""
        today = fields.Date.context_today(self)
        expired_contracts = self.search([
            ('state', '=', 'open'),
            ('date_end', '!=', False),
            ('date_end', '<', today),
        ])
        contracts_without_departure = expired_contracts.filtered(
            lambda contract: not contract.employee_id.departure_reason_id
        )
        contracts_with_departure = expired_contracts - contracts_without_departure
        if contracts_without_departure:
            contracts_without_departure.write({'state': 'close'})
        if contracts_with_departure:
            contracts_with_departure.write({'state': 'cancel'})
        return True

    def _send_contract_update_notification(self):
        distribution_list = self.env['zhr.mail.distribution.list'].sudo().search([
            ('name', '=', 'Avisos Contratos'),
            ('active', '=', True),
        ], limit=1)
        recipients = distribution_list._get_recipient_emails() if distribution_list else []
        if not recipients:
            return False

        body = self._get_contract_update_email_body()
        if not body:
            return False

        mail_values = {
            'subject': 'Odoo Actualizaciones Contratos',
            'email_to': ','.join(recipients),
            'body_html': body,
            'auto_delete': True,
        }
        self.env['mail.mail'].sudo().create(mail_values).send()
        return True

    def _get_contract_update_email_body(self):
        if not self:
            return False

        rows = []
        state_labels = dict(self.fields_get(['state'], ['selection'])['state']['selection'])
        for contract in self:
            rows.append(Markup(
                '<tr>'
                '<td>{employee}</td>'
                '<td>{date_start}</td>'
                '<td>{date_end}</td>'
                '<td>{state}</td>'
                '</tr>'
            ).format(
                employee=escape(contract.employee_id.name or ''),
                date_start=escape(contract.date_start or ''),
                date_end=escape(contract.date_end or ''),
                state=escape(state_labels.get(contract.state, contract.state or '')),
            ))

        return Markup(
            '<p>Se registraron actualizaciones en contratos de empleados:</p>'
            '<table border="1" cellpadding="5" cellspacing="0">'
            '<thead>'
            '<tr>'
            '<th>Nombre del empleado</th>'
            '<th>Fecha de inicio</th>'
            '<th>Fecha de término</th>'
            '<th>Estado del contrato</th>'
            '</tr>'
            '</thead>'
            '<tbody>{rows}</tbody>'
            '</table>'
        ).format(rows=Markup('').join(rows))

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
                rec.schedule_details = rec.resource_calendar_id.system_schedule
            else:
                rec.schedule_details = ""

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

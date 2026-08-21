import unicodedata

from babel.dates import format_date
from dateutil.relativedelta import relativedelta

from odoo import fields, models, api
from odoo.exceptions import ValidationError

REAL_CONTRACT_STATES = ('open', 'close', 'expired')

class HrContract(models.Model):
    _inherit = 'hr.contract'

    state = fields.Selection(
        selection_add=[('expired', 'Expirado'), ('cancel',)],
        ondelete={'expired': 'set default'},
    )

    identification_id = fields.Char(
        string='Numero de Identificacion',
        related='employee_id.identification_id',
        store=True,
        readonly=True,
    )
    fecha_contrato = fields.Date(
        string='Fecha Contrato',
        help=(
            'Fecha documental del contrato. Se cambia manualmente en la ficha '
            'del contrato y no modifica la vigencia legal del contrato.'
        ),
    )
    fecha_finiquito = fields.Date(
        string='Fecha Termino',
        help=(
            'Fecha documental de termino. Se actualiza al dar de baja al '
            'empleado para contratos vigentes o vencidos, y tambien puede '
            'editarse manualmente en el contrato.'
        ),
    )
    departure_reason_id = fields.Many2one(
        'hr.departure.reason',
        string='Motivo de Salida',
        help=(
            'Motivo historico de salida registrado al dar de baja al empleado. '
            'Se guarda en el contrato para conservar el dato aunque el '
            'trabajador sea dado de alta nuevamente.'
        ),
    )
    reference_id = fields.Many2one(
        'hr.contract.reference',
        string='Referencia del contrato',
        domain=[('active', '=', True)],
        help=(
            'Referencia documental del contrato o anexo. Al seleccionarla se '
            'concatena con el nombre del empleado para formar la referencia '
            'del contrato.'
        ),
    )

    schedule_pay = fields.Selection(
        [
            ('daily', 'Diario'),
            ('weekly', 'Semanal'),
            ('bi-weekly', 'Quincenal'),
            ('bi-monthly', 'Bimensual'),
            ('monthly', 'Mensual'),
            ('quarterly', 'Trimestral'),
            ('semi-annually', 'Semestral'),
            ('annually', 'Anual'),
        ],
        string='Periodicidad de pago',
        default='monthly',
    )

    wage_text = fields.Char(compute="_compute_wage_text")
    wage_positive_check = fields.Char(
        string='Salario',
        compute='_compute_wage_positive_check',
    )

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

    @api.depends('wage')
    def _compute_wage_positive_check(self):
        for contract in self:
            contract.wage_positive_check = 'ok' if contract.wage and contract.wage > 0 else False

    @api.constrains('wage')
    def _check_wage_positive(self):
        for contract in self:
            if not contract.wage or contract.wage <= 0:
                raise ValidationError(
                    'El salario del contrato debe ser mayor a 0.'
                )

    employee_payment_concept_ids = fields.One2many(
        'hr.employee.payment.concept',
        'contract_id',
        string='Conceptos de Pago',
    )

    tipo_obra_id = fields.Many2one(
        'hr.tipo.obra',
        string='Tipo de obra',
        help=(
            'Obra o faena asociada al contrato. Se cambia en la ficha del '
            'contrato cuando el contrato es por obra y se usa en los textos '
            'de contrato o anexos.'
        ),
    )

    duracion_obra = fields.Char(
        string='Duración de obra',
        help=(
            'Descripcion de la duracion estimada de la obra. Se cambia en la '
            'ficha del contrato y se usa en las clausulas impresas.'
        ),
    )
    
    lugar_trabajo_id = fields.Many2one(
        'hr.lugar.trabajo',
        string='Lugar de trabajo',
        help=(
            'Lugar de prestacion de servicios del contrato. Se cambia en la '
            'ficha del contrato y se usa en reportes e impresiones.'
        ),
    )
    is_por_obra = fields.Boolean(
        compute='_compute_is_por_obra',
    )

    lugar_trabajo_line_ids = fields.One2many(
        'hr.employee.lugar.trabajo',
        'contract_id',
        string='Lugares de trabajo',
    )
    is_indefinite_contract = fields.Boolean(
        compute='_compute_is_indefinite_contract',
    )
    can_edit_fecha_contrato = fields.Boolean(
        compute='_compute_can_edit_fecha_contrato',
    )

    @api.depends('contract_type_id')
    def _compute_is_por_obra(self):
        for rec in self:
            contract_type_name = (rec.contract_type_id.name or '').strip().lower()
            rec.is_por_obra = 'obra' in contract_type_name

    @api.depends('contract_type_id')
    def _compute_is_indefinite_contract(self):
        for rec in self:
            rec.is_indefinite_contract = rec._is_indefinite_contract_type(
                rec.contract_type_id
            )

    @api.depends('employee_id', 'fecha_contrato', 'date_start', 'reference_id')
    def _compute_can_edit_fecha_contrato(self):
        for contract in self:
            contract.can_edit_fecha_contrato = contract._can_edit_contract_date()

    @api.onchange('reference_id', 'employee_id')
    def _onchange_reference_id_employee_id(self):
        for contract in self:
            if contract.reference_id:
                contract.name = contract._build_reference_name(
                    contract.reference_id,
                    contract.employee_id,
                )

    @api.onchange('fecha_contrato')
    def _onchange_fecha_contrato(self):
        for contract in self:
            if (
                contract.fecha_contrato
                and (not contract._origin.id or not contract.date_start)
            ):
                contract.date_start = contract.fecha_contrato

    @api.onchange('fecha_finiquito')
    def _onchange_fecha_finiquito(self):
        for contract in self:
            if contract.fecha_finiquito:
                contract.date_end = contract.fecha_finiquito

    @api.onchange('date_start', 'date_end')
    def _onchange_contract_dates_state(self):
        for contract in self:
            if contract.state == 'cancel':
                continue
            today = fields.Date.context_today(contract)
            if contract.date_end:
                contract.state = 'open' if contract.date_end >= today else 'close'
                continue
            if (
                contract._origin.id
                and contract.date_start
                and contract.date_start >= today
            ):
                contract.state = 'open'

    @api.onchange('contract_type_id')
    def _onchange_contract_type_id_indefinite_dates(self):
        for contract in self:
            if contract._is_indefinite_contract_type(contract.contract_type_id):
                contract.date_end = False
                contract.fecha_finiquito = False

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            self._prepare_reference_name(vals)
            self._prepare_preserved_contract_date(vals)
            self._prepare_contract_dates(vals)
        contracts = super().create(vals_list)
        contracts._close_previous_open_contracts()
        contracts._check_contract_date_continuity()
        contracts._sync_employee_work_dates()
        return contracts

    def write(self, vals):
        if self.env.context.get('skip_contract_continuity_sync'):
            return super().write(vals)

        employees = self.mapped('employee_id')
        sync_fields = {
            'employee_id',
            'state',
            'date_start',
            'date_end',
            'fecha_contrato',
            'fecha_finiquito',
            'job_id',
            'department_id',
            'resource_calendar_id',
            'work_location_id',
        }
        should_sync = bool(sync_fields.intersection(vals))

        if 'reference_id' not in vals and 'employee_id' not in vals:
            vals = dict(vals)
            if 'fecha_contrato' in vals:
                self._prepare_preserved_contract_date(vals)
            self._prepare_contract_dates(vals)
            if len(self) == 1:
                self._prepare_state_from_contract_dates(vals)
            result = super().write(vals)
            self._close_previous_open_contracts()
            self._check_contract_date_continuity()
            if should_sync:
                (employees | self.mapped('employee_id'))._sync_contract_work_dates()
            return result

        for contract in self:
            contract_vals = dict(vals)
            contract._prepare_reference_name(contract_vals)
            contract._prepare_preserved_contract_date(contract_vals)
            contract._prepare_contract_dates(contract_vals)
            contract._prepare_state_from_contract_dates(contract_vals)
            super(HrContract, contract).write(contract_vals)
        self._close_previous_open_contracts()
        self._check_contract_date_continuity()
        if should_sync:
            (employees | self.mapped('employee_id'))._sync_contract_work_dates()
        return True

    def unlink(self):
        employees = self.mapped('employee_id')
        result = super().unlink()
        employees._sync_contract_work_dates(clear_without_open=True)
        return result

    def _sync_employee_work_dates(self):
        self.mapped('employee_id')._sync_contract_work_dates()

    def _close_previous_open_contracts(self):
        if not self.env.context.get('close_previous_contract'):
            return

        for contract in self.sudo():
            if (
                not contract.employee_id
                or not contract.date_start
                or contract.state not in REAL_CONTRACT_STATES
                or contract._is_renewal_annex()
            ):
                continue

            previous_open_contract = contract.sudo().search(
                [
                    ('employee_id', '=', contract.employee_id.id),
                    ('id', '!=', contract.id),
                    ('state', '=', 'open'),
                    ('date_start', '<', contract.date_start),
                ],
                order='date_start desc, id desc',
                limit=1,
            )
            if not previous_open_contract:
                continue

            previous_open_contract.with_context(
                skip_contract_continuity_sync=True
            ).write({
                'date_end': contract.date_start - relativedelta(days=1),
                'state': 'expired',
            })

    def _check_contract_date_continuity(self):
        employees = self.mapped('employee_id')
        for employee in employees.sudo():
            contracts = self.sudo().search(
                [
                    ('employee_id', '=', employee.id),
                    ('state', 'in', REAL_CONTRACT_STATES),
                    ('date_start', '!=', False),
                ],
                order='date_start, id',
            )
            contracts = contracts.filtered(
                lambda contract: contract._participates_in_contract_continuity()
            )
            previous_contract = self.env['hr.contract']
            for contract in contracts:
                if previous_contract:
                    contract._check_against_previous_contract(previous_contract)
                previous_contract = contract

    def _check_against_previous_contract(self, previous_contract):
        self.ensure_one()
        if not previous_contract.date_end:
            raise ValidationError(
                'No puede guardar el contrato "%s" porque se superpone con '
                'el contrato anterior "%s", que no tiene fecha de finalizacion.'
                % (self.display_name, previous_contract.display_name)
            )

        if self.date_start <= previous_contract.date_end:
            raise ValidationError(
                'No puede guardar el contrato "%s" porque se superpone con '
                'el contrato anterior "%s". Revise las fechas de vigencia.'
                % (self.display_name, previous_contract.display_name)
            )

        expected_start = previous_contract.date_end + relativedelta(days=1)
        if self.date_start > expected_start:
            raise ValidationError(
                'No puede guardar el contrato "%s" porque existe un vacio '
                'contractual entre el %s y el %s. Revise las fechas de '
                'vigencia.'
                % (
                    self.display_name,
                    expected_start.strftime('%d/%m/%Y'),
                    (self.date_start - relativedelta(days=1)).strftime('%d/%m/%Y'),
                )
            )

    def _prepare_contract_dates(self, vals):
        if (
            vals.get('fecha_contrato')
            and 'date_start' not in vals
            and (not self or (len(self) == 1 and not self.date_start))
        ):
            vals['date_start'] = vals['fecha_contrato']
        if vals.get('fecha_finiquito') and 'date_end' not in vals:
            vals['date_end'] = vals['fecha_finiquito']

    def _prepare_state_from_contract_dates(self, vals):
        if 'state' in vals:
            return
        current_state = self.state if len(self) == 1 else False
        if current_state == 'cancel':
            return

        if vals.get('date_end'):
            date_end = fields.Date.to_date(vals['date_end'])
            vals['state'] = (
                'open'
                if date_end >= fields.Date.context_today(self)
                else 'close'
            )
            return

        if 'date_start' not in vals or not vals.get('date_start'):
            return
        date_start = fields.Date.to_date(vals['date_start'])
        if date_start and date_start >= fields.Date.context_today(self):
            vals['state'] = 'open'

    def _prepare_preserved_contract_date(self, vals):
        if self.env.context.get('skip_preserve_contract_date'):
            return

        reference_id = vals.get('reference_id', self.reference_id.id if self else False)
        if not self._should_preserve_contract_date(reference_id):
            return

        # "Contrato" is the authoritative document: an explicitly entered
        # date must win over dates inherited from deleted, historical or
        # previously active contracts. Annexes and settlements still preserve
        # the contract date as before.
        if (
            'fecha_contrato' in vals
            and self._is_contract_reference(reference_id)
        ):
            return

        employee_id = vals.get('employee_id', self.employee_id.id if self else False)
        preserved_date = self._get_preserved_contract_date(employee_id)
        if preserved_date:
            vals['fecha_contrato'] = preserved_date

    def _should_preserve_contract_date(self, reference_id):
        return bool(reference_id)

    def _is_contract_reference(self, reference_id):
        if not reference_id:
            return False
        contract_reference = self.env.ref(
            'zhr_ajustes.hr_contract_reference_contract',
            raise_if_not_found=False,
        )
        return bool(contract_reference and reference_id == contract_reference.id)

    def _is_renewal_annex(self):
        self.ensure_one()
        return self._is_renewal_annex_reference(self.reference_id)

    def _participates_in_contract_continuity(self):
        self.ensure_one()
        return not (
            self.reference_id
            and self.reference_id.reference_type == 'annex'
        )

    def _is_annex_reference(self, reference):
        if not reference:
            return False
        if isinstance(reference, int):
            reference = self.env['hr.contract.reference'].browse(reference)
        return reference.reference_type == 'annex'

    def _is_renewal_annex_reference(self, reference):
        if not reference:
            return False
        if isinstance(reference, int):
            reference = self.env['hr.contract.reference'].browse(reference)

        normalized_name = unicodedata.normalize(
            'NFKD',
            reference.name or '',
        ).encode('ascii', 'ignore').decode('ascii').strip().lower()
        return normalized_name in (
            'anexo renovacion',
            'anexo renovacion indefinido',
        )

    def _is_indefinite_renewal_annex_reference(self, reference):
        if not reference:
            return False
        if isinstance(reference, int):
            reference = self.env['hr.contract.reference'].browse(reference)

        normalized_name = unicodedata.normalize(
            'NFKD',
            reference.name or '',
        ).encode('ascii', 'ignore').decode('ascii').strip().lower()
        return normalized_name == 'anexo renovacion indefinido'

    def _get_indefinite_contract_type(self):
        return self.env['hr.contract.type'].search(
            [('name', '=ilike', 'Indefinido')],
            limit=1,
        )

    def _is_indefinite_contract_type(self, contract_type):
        return bool(
            contract_type
            and (contract_type.name or '').strip().lower() == 'indefinido'
        )

    def _can_edit_contract_date(self):
        self.ensure_one()
        if not self.id or not self.employee_id:
            return True
        if self._is_contract_reference(self.reference_id.id):
            return True
        first_contract = self._get_first_real_contract(self.employee_id.id)
        return not first_contract or first_contract == self

    def _get_first_real_contract(self, employee_id):
        if not employee_id:
            return self.env['hr.contract']

        contracts = self.sudo().search(
            [
                ('employee_id', '=', employee_id),
                '|',
                ('fecha_contrato', '!=', False),
                ('date_start', '!=', False),
            ],
            order='fecha_contrato, date_start, id',
        )
        return contracts.filtered(
            lambda contract: contract._is_first_contract_candidate()
        )[:1]

    def _is_first_contract_candidate(self):
        self.ensure_one()
        reference_name = self.reference_id.name or ''
        normalized_name = unicodedata.normalize(
            'NFKD',
            reference_name,
        ).encode('ascii', 'ignore').decode('ascii').strip().lower()
        return not (
            normalized_name.startswith('anexo')
            or normalized_name == 'finiquito'
        )

    def _get_preserved_contract_date(self, employee_id=False):
        if len(self) == 1 and self.fecha_contrato:
            return self.fecha_contrato

        if not employee_id:
            return False

        employee = self.env['hr.employee'].sudo().browse(employee_id)
        if employee.fecha_contrato:
            return employee.fecha_contrato

        return self._get_employee_first_contract_date(employee_id)

    def _get_employee_first_contract_date(self, employee_id):
        if not employee_id:
            return False

        current_id = self.id if len(self) == 1 else False
        domain = [
            ('employee_id', '=', employee_id),
            ('id', '!=', current_id),
            ('state', '!=', 'cancel'),
            ('fecha_contrato', '!=', False),
        ]
        contract_reference = self.env.ref(
            'zhr_ajustes.hr_contract_reference_contract',
            raise_if_not_found=False,
        )
        if contract_reference:
            domain.append(('reference_id', '=', contract_reference.id))

        contract = self.sudo().search(
            domain,
            order='fecha_contrato, date_start, id',
            limit=1,
        )
        if contract:
            return contract.fecha_contrato

        contract = self.sudo().search(
            [
                ('employee_id', '=', employee_id),
                ('id', '!=', current_id),
                ('state', '!=', 'cancel'),
                '|',
                ('fecha_contrato', '!=', False),
                ('date_start', '!=', False),
            ],
            order='fecha_contrato, date_start, id',
            limit=1,
        )
        return contract.fecha_contrato or contract.date_start if contract else False

    def _prepare_reference_name(self, vals):
        reference_id = vals.get('reference_id', self.reference_id.id if self else False)
        if not reference_id:
            return

        employee_id = vals.get('employee_id', self.employee_id.id if self else False)
        reference = self.env['hr.contract.reference'].browse(reference_id)
        employee = self.env['hr.employee'].browse(employee_id) if employee_id else self.env['hr.employee']
        vals['name'] = self._build_reference_name(reference, employee)

    @api.model
    def _build_reference_name(self, reference, employee):
        return ' - '.join(
            part
            for part in (reference.name or '', employee.name or '')
            if part
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

    def action_open_mass_print_wizard(self):
        contracts = self or self.browse(self.env.context.get('active_ids', []))
        wizard = self.env['hr.contract.mass.print.wizard'].create({
            'contract_ids': [(6, 0, contracts.ids)],
        })
        return {
            'type': 'ir.actions.act_window',
            'name': 'Impresion masiva de contratos',
            'res_model': 'hr.contract.mass.print.wizard',
            'view_mode': 'form',
            'res_id': wizard.id,
            'target': 'new',
        }

    def action_open_duplicate_wizard(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Duplicar contrato',
            'res_model': 'hr.contract.duplicate.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_contract_id': self.id,
            },
        }

    def action_duplicate_with_new_reference(self, date_start, name, reference_id=False):
        self.ensure_one()
        if date_start <= self.date_start:
            raise ValidationError(
                'La nueva fecha de inicio debe ser posterior a la fecha '
                'de inicio del contrato actual.'
            )

        should_preserve_contract_date = self._should_preserve_contract_date(reference_id)
        is_renewal_annex = self._is_renewal_annex_reference(reference_id)
        is_annex_reference = self._is_annex_reference(reference_id)
        is_indefinite_renewal_annex = self._is_indefinite_renewal_annex_reference(reference_id)
        preserved_date = (
            self._get_preserved_contract_date(self.employee_id.id)
            if should_preserve_contract_date
            else date_start
        )
        new_contract_vals = {
            'name': name,
            'fecha_contrato': preserved_date or date_start,
            'date_start': date_start,
            'date_end': False,
            'fecha_finiquito': False,
            'departure_reason_id': False,
            'state': 'open',
            'kanban_state': 'normal',
            'reference_id': reference_id or False,
        }
        if is_annex_reference:
            annex_end_date = self.fecha_finiquito or self.date_end
            if annex_end_date:
                new_contract_vals.update({
                    'date_end': annex_end_date,
                    'fecha_finiquito': annex_end_date,
                })
        if is_indefinite_renewal_annex:
            indefinite_contract_type = self._get_indefinite_contract_type()
            if indefinite_contract_type:
                new_contract_vals['contract_type_id'] = indefinite_contract_type.id

        origin_vals = {'state': 'expired'}
        if not self.date_end:
            origin_vals['date_end'] = date_start - relativedelta(days=1)
        elif not is_renewal_annex and not is_annex_reference:
            origin_vals['date_end'] = date_start - relativedelta(days=1)
        if self.state != 'cancel':
            self.write(origin_vals)

        new_contract = self.copy(new_contract_vals)
        return new_contract

    schedule_details = fields.Text(
        compute="_compute_schedule_details",
        help=(
            'Detalle del horario tomado desde el calendario de trabajo del '
            'contrato. Cambia al modificar el horario de trabajo asociado.'
        ),
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

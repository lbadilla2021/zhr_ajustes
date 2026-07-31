import re

import unicodedata

from odoo import api, fields, models
from odoo.exceptions import ValidationError


EMPLOYEE_READONLY_GROUP = 'zhr_ajustes.group_zhr_employee_readonly'
HR_PRIVATE_GROUP = 'hr.group_hr_user'
CUSTOM_PRIVATE_EMPLOYEE_FIELDS = {
    'rut_dv',
    'apellido_paterno',
    'apellido_materno',
    'nombres',
    'nombre_preferido',
    'city_id',
    'driver_license_expiration_date',
    'analytic_account_id',
    'afp_id',
    'health_system_id',
    'system_schedule',
    'fecha_contrato',
    'fecha_finiquito',
    'fecha_primer_ingreso',
    'state',
    'accreditation_ids',
    'assigned_resource_ids',
    'payment_concept_line_ids',
    'lugar_trabajo_line_ids',
}
READONLY_PRIVATE_EMPLOYEE_FIELDS = (
    'company_country_id',
    'company_country_code',
    'private_street',
    'private_street2',
    'private_city',
    'private_state_id',
    'private_zip',
    'private_country_id',
    'private_phone',
    'private_email',
    'lang',
    'country_id',
    'gender',
    'marital',
    'spouse_complete_name',
    'spouse_birthdate',
    'children',
    'place_of_birth',
    'country_of_birth',
    'birthday',
    'ssnid',
    'sinid',
    'identification_id',
    'passport_id',
    'bank_account_id',
    'permit_no',
    'visa_no',
    'visa_expire',
    'work_permit_expiration_date',
    'has_work_permit',
    'additional_note',
    'certificate',
    'study_field',
    'study_school',
    'emergency_contact',
    'emergency_phone',
    'distance_home_work',
    'km_home_work',
    'distance_home_work_unit',
    'employee_type',
    'category_ids',
    'notes',
    'barcode',
    'pin',
    'departure_reason_id',
    'departure_description',
    'departure_date',
    'message_main_attachment_id',
    'message_is_follower',
    'message_follower_ids',
    'message_partner_ids',
    'message_ids',
    'has_message',
    'message_needaction',
    'message_needaction_counter',
    'message_has_error',
    'message_has_error_counter',
    'message_attachment_count',
    'activity_ids',
    'activity_state',
    'activity_user_id',
    'activity_type_id',
    'activity_type_icon',
    'activity_date_deadline',
    'my_activity_date_deadline',
    'activity_summary',
    'activity_exception_decoration',
    'activity_exception_icon',
    'id_card',
    'driving_license',
    'private_car_plate',
    'currency_id',
    'calendar_mismatch',
    'contracts_count',
    'contract_warning',
    'current_leave_id',
    'current_leave_state',
    'first_contract_date',
    'leave_date_from',
    'leave_date_to',
    'is_absent',
    'show_leaves',
    'allocation_display',
    'allocation_remaining_display',
    'hr_icon_display',
    'rut_dv',
    'apellido_paterno',
    'apellido_materno',
    'nombres',
    'nombre_preferido',
    'city_id',
    'driver_license_expiration_date',
    'analytic_account_id',
    'afp_id',
    'health_system_id',
    'system_schedule',
    'fecha_contrato',
    'fecha_finiquito',
    'fecha_primer_ingreso',
    'state',
    'accreditation_ids',
    'assigned_resource_ids',
    'payment_concept_line_ids',
    'lugar_trabajo_line_ids',
)

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    def _setup_complete(self):
        super()._setup_complete()
        for field_name in READONLY_PRIVATE_EMPLOYEE_FIELDS:
            field = self._fields.get(field_name)
            if not field:
                continue
            groups = [group for group in (field.groups or '').split(',') if group]
            if not groups and field_name not in CUSTOM_PRIVATE_EMPLOYEE_FIELDS:
                continue
            if not groups and HR_PRIVATE_GROUP not in groups:
                groups.append(HR_PRIVATE_GROUP)
            if EMPLOYEE_READONLY_GROUP not in groups:
                groups.append(EMPLOYEE_READONLY_GROUP)
            field.groups = ','.join(groups)

    rut_dv = fields.Char(string='Digito Verificador', size=1)
    apellido_paterno = fields.Char(string='Apellido Paterno')
    apellido_materno = fields.Char(string='Apellido Materno')
    nombres = fields.Char(string='Nombres')
    nombre_preferido = fields.Char(string='Nombre Preferido')
    city_id = fields.Many2one('hr.city', string='Ciudad')
    driver_license_expiration_date = fields.Date(
        string='Vencimiento licencia conducir',
    )
    fecha_contrato = fields.Date(
        string='Fecha Contrato',
        help=(
            'Fecha documental asociada al contrato vigente del trabajador. Se '
            'actualiza desde el boton Dar de Alta o al guardar un contrato en '
            'estado Vigente.'
        ),
    )
    fecha_finiquito = fields.Date(
        string='Fecha Termino',
        help=(
            'Fecha documental de termino del trabajador. Se actualiza desde '
            'el boton Dar de Baja usando la fecha de salida digitada.'
        ),
    )
    fecha_primer_ingreso = fields.Date(
        string='Fecha primer ingreso',
        help=(
            'Fecha historica del primer ingreso del trabajador. Se toma desde '
            'el primer contrato real y no se modifica por anexos, finiquitos '
            'o altas posteriores.'
        ),
    )
    analytic_account_id = fields.Many2one(
        'account.analytic.account',
        string='Centro de Costo',
        domain="[('company_id', '=', company_id)]",
        help='Seleccione el centro de costo dentro del plan analítico de la empresa.',
    )
    job_family_id = fields.Many2one(
        'hr.job.family',
        string='Familia',
        related='job_id.job_family_id',
        store=True,
        readonly=True,
    )
    afp_id = fields.Many2one('hr.afp', string='AFP')
    health_system_id = fields.Many2one('hr.health_system', string='Sistema de Salud')
    system_schedule = fields.Char(
        string='Sistema Horario',
        related='resource_calendar_id.system_schedule',
        store=True,
        readonly=True,
    )
    is_active_employee = fields.Boolean(
        compute='_compute_is_active_employee',
        store=False,
    )
    hide_resume_for_readonly = fields.Boolean(
        compute='_compute_hide_resume_for_readonly',
        store=False,
    )
    state = fields.Selection(
        [('active', 'Activo'), ('inactive', 'Inactivo')],
        string='Estado',
        default='active',
        required=True,
    )
    accreditation_ids = fields.One2many(
        'hr.employee.accreditation',
        'employee_id',
        string='Acreditaciones',
    )

    assigned_resource_ids = fields.One2many(
        'hr.employee.assigned.resource',
        'employee_id',
        string='Recursos Asignados',
    )

    payment_concept_line_ids = fields.One2many(
        'hr.employee.payment.concept',
        'employee_id',
        string='Conceptos de Pago',
    )

    lugar_trabajo_line_ids = fields.One2many(
        'hr.employee.lugar.trabajo',
        'employee_id',
        string='Lugar de trabajo',
    )

    @api.onchange('nombres', 'apellido_paterno', 'apellido_materno')
    def _onchange_employee_full_name(self):
        for employee in self:
            employee.name = employee._build_employee_name()

    @api.onchange('city_id')
    def _onchange_city_id(self):
        for employee in self:
            employee.private_city = employee.city_id.name if employee.city_id else False

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            self._prepare_employee_vals(vals)
        return super().create(vals_list)

    def write(self, vals):
        name_fields = {'nombres', 'apellido_paterno', 'apellido_materno'}
        if len(self) > 1 and name_fields.intersection(vals):
            for employee in self:
                employee_vals = dict(vals)
                employee._prepare_employee_vals(employee_vals)
                super(HrEmployee, employee).write(employee_vals)
            return True

        vals = dict(vals)
        self._prepare_employee_vals(vals)
        return super().write(vals)

    def _prepare_employee_vals(self, vals):
        employee = self[:1]
        name_fields = {'nombres', 'apellido_paterno', 'apellido_materno'}
        if name_fields.intersection(vals):
            vals['name'] = self._build_employee_name_from_values(
                vals.get('nombres', employee.nombres if employee else False),
                vals.get(
                    'apellido_paterno',
                    employee.apellido_paterno if employee else False,
                ),
                vals.get(
                    'apellido_materno',
                    employee.apellido_materno if employee else False,
                ),
            )

        if vals.get('city_id'):
            vals['private_city'] = self.env['hr.city'].browse(vals['city_id']).name
        elif 'city_id' in vals:
            vals['private_city'] = False

    def _sync_contract_work_dates(self, clear_without_open=False):
        for employee in self.with_context(active_test=False).sudo():
            contracts = employee.contract_ids.sudo()
            open_contracts = contracts.filtered(
                lambda contract: (
                    contract.state == 'open'
                    and contract._participates_in_contract_continuity()
                )
            ).sorted(key=lambda contract: (
                contract.date_start or contract.fecha_contrato or fields.Date.to_date('0001-01-01'),
                contract.id,
            ))
            if not open_contracts:
                if clear_without_open:
                    vals = {
                        'fecha_contrato': False,
                        'fecha_finiquito': False,
                    }
                    if not contracts:
                        vals['fecha_primer_ingreso'] = False
                    elif not employee.fecha_primer_ingreso:
                        first_entry_date = employee._get_first_entry_contract_date(contracts)
                        if first_entry_date:
                            vals['fecha_primer_ingreso'] = first_entry_date
                    employee.write(vals)
                continue

            current_contract = open_contracts[-1]
            vals = {
                'fecha_contrato': current_contract.fecha_contrato
                or current_contract.date_start,
                'fecha_finiquito': current_contract.fecha_finiquito,
            }
            vals.update(employee._get_contract_employee_sync_vals(current_contract))

            first_entry_date = employee._get_first_entry_contract_date(contracts)
            if first_entry_date and not employee.fecha_primer_ingreso:
                vals['fecha_primer_ingreso'] = first_entry_date
            if vals:
                employee.write(vals)

    def _get_contract_employee_sync_vals(self, contract):
        self.ensure_one()
        vals = {}
        field_map = {
            'job_id': 'job_id',
            'department_id': 'department_id',
            'resource_calendar_id': 'resource_calendar_id',
            'work_location_id': 'work_location_id',
        }
        for contract_field, employee_field in field_map.items():
            if contract_field not in contract._fields or employee_field not in self._fields:
                continue
            vals[employee_field] = contract[contract_field].id or False
        return vals

    def _get_first_entry_contract_date(self, contracts):
        self.ensure_one()
        valid_contracts = contracts.filtered(
            lambda contract: (
                (contract.date_start or contract.fecha_contrato)
                and self._is_first_entry_contract_candidate(contract)
            )
        )
        if not valid_contracts:
            return False

        return min(
            contract.date_start or contract.fecha_contrato
            for contract in valid_contracts
            if contract.date_start or contract.fecha_contrato
        )

    def _is_first_entry_contract_candidate(self, contract):
        reference_name = contract.reference_id.name or ''
        normalized_name = unicodedata.normalize(
            'NFKD',
            reference_name,
        ).encode('ascii', 'ignore').decode('ascii').strip().lower()
        return not (
            normalized_name.startswith('anexo')
            or normalized_name == 'finiquito'
        )

    def _build_employee_name(self):
        self.ensure_one()
        return self._build_employee_name_from_values(
            self.nombres,
            self.apellido_paterno,
            self.apellido_materno,
        )

    @api.model
    def _build_employee_name_from_values(
        self,
        nombres,
        apellido_paterno,
        apellido_materno,
    ):
        return ' '.join(
            part.strip()
            for part in (nombres, apellido_paterno, apellido_materno)
            if part and part.strip()
        )

    @api.onchange('identification_id')
    def _onchange_identification_id_rut(self):
        for employee in self:
            if not employee.identification_id:
                continue

            duplicate = employee._find_employee_with_same_rut()
            if duplicate:
                employee.identification_id = False
                employee.rut_dv = False
                return {
                    'warning': {
                        'title': 'RUT duplicado',
                        'message': (
                            'El numero de identificacion ya pertenece al empleado %s. '
                            'El campo fue limpiado para evitar continuar con un duplicado.'
                        ) % duplicate.display_name,
                    },
                }

    @api.onchange('rut_dv')
    def _onchange_rut_dv(self):
        for employee in self:
            employee.rut_dv = employee._normalize_rut_dv(employee.rut_dv)
            if not employee.identification_id or not employee.rut_dv:
                continue

            if not employee._is_valid_rut():
                employee.rut_dv = False
                return {
                    'warning': {
                        'title': 'RUT incorrecto',
                        'message': (
                            'El digito verificador no corresponde al numero de '
                            'identificacion ingresado.'
                        ),
                    },
                }

    @api.constrains('identification_id', 'rut_dv')
    def _check_employee_rut(self):
        for employee in self:
            if not employee.identification_id:
                continue

            duplicate = employee._find_employee_with_same_rut()
            if duplicate:
                raise ValidationError(
                    'El numero de identificacion ya pertenece al empleado %s.'
                    % duplicate.display_name
                )

            if not employee.rut_dv:
                raise ValidationError(
                    'Debe ingresar el digito verificador del RUT.'
                )

            if not employee._is_valid_rut():
                raise ValidationError(
                    'El RUT ingresado no es valido. Revise el numero de '
                    'identificacion y su digito verificador.'
                )

    def _find_employee_with_same_rut(self):
        self.ensure_one()
        rut_base = self._normalize_rut_base(self.identification_id)
        if not rut_base:
            return self.env['hr.employee']

        current_id = self._origin.id if self._origin else self.id
        if not isinstance(current_id, int):
            current_id = False

        domain = [('id', '!=', current_id)] if current_id else []
        employees = self.sudo().with_context(active_test=False).search(domain)
        for employee in employees:
            if self._normalize_rut_base(employee.identification_id) == rut_base:
                return employee
        return self.env['hr.employee']

    def _is_valid_rut(self):
        self.ensure_one()
        rut_base = self._normalize_rut_base(self.identification_id)
        rut_dv = self._normalize_rut_dv(self.rut_dv)
        if not rut_base or not rut_base.isdigit() or len(rut_dv) != 1:
            return False
        return self._calculate_rut_dv(rut_base) == rut_dv

    @api.model
    def _normalize_rut_base(self, value):
        value = (value or '').strip()
        if '-' in value:
            value = value.split('-', 1)[0]
        return re.sub(r'\D', '', value)

    @api.model
    def _normalize_rut_dv(self, value):
        return re.sub(r'[^0-9Kk]', '', value or '').upper()

    @api.model
    def _calculate_rut_dv(self, rut_base):
        factors = [2, 3, 4, 5, 6, 7]
        total = sum(
            int(digit) * factors[index % len(factors)]
            for index, digit in enumerate(reversed(rut_base))
        )
        result = 11 - (total % 11)
        if result == 11:
            return '0'
        if result == 10:
            return 'K'
        return str(result)

    @api.depends('state')
    def _compute_is_active_employee(self):
        for rec in self:
            rec.is_active_employee = rec.state == 'active'

    def _compute_hide_resume_for_readonly(self):
        hide_resume = self.env.user.has_group(EMPLOYEE_READONLY_GROUP)
        for rec in self:
            rec.hide_resume_for_readonly = hide_resume

    def action_open_termination_wizard(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Dar de Baja',
            'res_model': 'hr.employee.termination.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_employee_id': self.id,
            },
        }

    def action_open_reactivation_wizard(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Dar de Alta',
            'res_model': 'hr.employee.reactivation.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_employee_id': self.id,
            },
        }

    # --- método correcto dentro de la clase ---
    def get_marital_label(self):
        self.ensure_one()
        # obtenemos las opciones de selección del campo 'marital'
        selection_dict = dict(self.fields_get(['marital'], ['selection'])['marital']['selection'])
        # devolvemos la etiqueta correspondiente al valor actual
        return selection_dict.get(self.marital, '')

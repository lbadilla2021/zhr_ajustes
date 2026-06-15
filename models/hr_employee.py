import re

from odoo import api, fields, models
from odoo.exceptions import ValidationError

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    rut_dv = fields.Char(string='Digito Verificador', size=1)
    apellido_paterno = fields.Char(string='Apellido Paterno')
    apellido_materno = fields.Char(string='Apellido Materno')
    nombres = fields.Char(string='Nombres')
    nombre_preferido = fields.Char(string='Nombre Preferido')
    city_id = fields.Many2one('hr.city', string='Ciudad')
    driver_license_expiration_date = fields.Date(
        string='Vencimiento licencia conducir',
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

    # --- método correcto dentro de la clase ---
    def get_marital_label(self):
        self.ensure_one()
        # obtenemos las opciones de selección del campo 'marital'
        selection_dict = dict(self.fields_get(['marital'], ['selection'])['marital']['selection'])
        # devolvemos la etiqueta correspondiente al valor actual
        return selection_dict.get(self.marital, '')

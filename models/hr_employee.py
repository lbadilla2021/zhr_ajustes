from odoo import api, fields, models


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    apellido_paterno = fields.Char(string='Apellido Paterno')
    apellido_materno = fields.Char(string='Apellido Materno')
    nombres = fields.Char(string='Nombres')
    nombre_preferido = fields.Char(string='Nombre Preferido')
    analytic_account_id = fields.Many2one(
        'account.analytic.account',
        string='Centro de Costo',
        domain="[('plan_id', 'child_of', plan_id)]",
        help='Seleccione el centro de costo dentro del plan analítico de la empresa.',
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

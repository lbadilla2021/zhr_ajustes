from odoo import SUPERUSER_ID, api


def post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    model = env['ir.model'].search([('model', '=', 'hr.system.schedule')], limit=1)
    if not model:
        return

    access = env['ir.model.access'].search(
        [('name', '=', 'access_hr_system_schedule'), ('model_id', '=', model.id)],
        limit=1,
    )
    if not access:
        env['ir.model.access'].create(
            {
                'name': 'access_hr_system_schedule',
                'model_id': model.id,
                'perm_read': True,
                'perm_write': True,
                'perm_create': True,
                'perm_unlink': True,
            }
        )

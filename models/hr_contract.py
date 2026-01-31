# -*- coding: utf-8 -*-
from odoo import fields, models


class HrContract(models.Model):
    _inherit = 'hr.contract'

    system_schedule_id = fields.Many2one(
        'hr.system.schedule',
        string='Sistema Horario',
    )

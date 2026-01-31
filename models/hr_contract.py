# -*- coding: utf-8 -*-
from odoo import fields, models


class HrContract(models.Model):
    _inherit = 'hr.contract'

    system_schedule = fields.Char(
        string='Sistema Horario',
        related='resource_calendar_id.system_schedule',
        readonly=True,
    )

from odoo import api, fields, models


class ZhrMailDistributionList(models.Model):
    _name = 'zhr.mail.distribution.list'
    _description = 'Lista de Distribución de Correos RRHH'
    _order = 'name'

    name = fields.Char(required=True)
    active = fields.Boolean(default=True)
    line_ids = fields.One2many(
        'zhr.mail.distribution.list.line',
        'list_id',
        string='Correos',
    )

    _sql_constraints = [
        ('name_unique', 'unique(name)', 'El nombre de la lista de distribución debe ser único.'),
    ]

    def _get_recipient_emails(self):
        self.ensure_one()
        emails = []
        seen = set()
        for line in self.line_ids.filtered('email'):
            normalized_email = line.email.strip().lower()
            if normalized_email and normalized_email not in seen:
                emails.append(normalized_email)
                seen.add(normalized_email)
        return emails


class ZhrMailDistributionListLine(models.Model):
    _name = 'zhr.mail.distribution.list.line'
    _description = 'Correo de Lista de Distribución RRHH'
    _order = 'email'

    list_id = fields.Many2one(
        'zhr.mail.distribution.list',
        string='Lista de Distribución',
        required=True,
        ondelete='cascade',
    )
    name = fields.Char(string='Nombre')
    email = fields.Char(required=True)

    @api.onchange('email')
    def _onchange_email(self):
        for line in self:
            if line.email:
                line.email = line.email.strip().lower()

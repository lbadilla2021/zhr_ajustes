import re
import unicodedata

from odoo import api, fields, models
from odoo.exceptions import ValidationError


CHILEAN_CITIES_BY_STATE = {
    'CL-BI': (
        'Alto Biobío',
        'Antuco',
        'Arauco',
        'Cabrero',
        'Cañete',
        'Chiguayante',
        'Concepción',
        'Contulmo',
        'Coronel',
        'Curanilahue',
        'Florida',
        'Hualpén',
        'Hualqui',
        'Laja',
        'Las Vegas',
        'Lebu',
        'Los Álamos',
        'Los Ángeles',
        'Lota',
        'Mulchén',
        'Nacimiento',
        'Negrete',
        'Penco',
        'Quilaco',
        'Quilleco',
        'San Pedro de la Paz',
        'San Rosendo',
        'Santa Bárbara',
        'Santa Juana',
        'Talcahuano',
        'Tirúa',
        'Tomé',
        'Tucapel',
        'Yumbel',
    ),
    'CL-AR': (
        'Angol',
        'Carahue',
        'Cholchol',
        'Collipulli',
        'Cunco',
        'Curacautín',
        'Curarrehue',
        'Ercilla',
        'Freire',
        'Galvarino',
        'Gorbea',
        'Lautaro',
        'Loncoche',
        'Lonquimay',
        'Los Sauces',
        'Lumaco',
        'Melipeuco',
        'Nueva Imperial',
        'Padre Las Casas',
        'Perquenco',
        'Pitrufquén',
        'Pucón',
        'Puerto Saavedra',
        'Purén',
        'Renaico',
        'Temuco',
        'Teodoro Schmidt',
        'Toltén',
        'Traiguén',
        'Victoria',
        'Vilcún',
        'Villarrica',
    ),
    'CL-NB': (
        'Bulnes',
        'Chillán',
        'Chillán Viejo',
        'Cobquecura',
        'Coelemu',
        'Coihueco',
        'El Carmen',
        'Ninhue',
        'Pemuco',
        'Pinto',
        'Portezuelo',
        'Quillón',
        'Quirihue',
        'Ránquil',
        'San Carlos',
        'San Fabián',
        'San Ignacio',
        'San Nicolás',
        'Treguaco',
        'Yungay',
        'Ñiquén',
    ),
    'CL-RM': ('Santiago',),
}


class HrCity(models.Model):
    _name = 'hr.city'
    _description = 'Ciudad'
    _order = 'name'

    name = fields.Char(string='Ciudad', required=True)
    country_id = fields.Many2one(
        'res.country',
        string='País',
        default=lambda self: self.env.ref('base.cl', raise_if_not_found=False),
        ondelete='restrict',
    )
    state_id = fields.Many2one(
        'res.country.state',
        string='Región',
        domain="[('country_id', '=', country_id)]",
        ondelete='restrict',
        index=True,
    )
    active = fields.Boolean(default=True)

    _sql_constraints = [
        (
            'name_state_unique',
            'unique(name, state_id)',
            'La ciudad ya existe en esta región.',
        ),
    ]

    @api.constrains('country_id', 'state_id')
    def _check_state_country(self):
        for city in self:
            if (
                city.country_id
                and city.state_id
                and city.state_id.country_id != city.country_id
            ):
                raise ValidationError(
                    'La región seleccionada no pertenece al país de la ciudad.'
                )

    @api.onchange('country_id')
    def _onchange_country_id(self):
        if self.state_id.country_id != self.country_id:
            self.state_id = False

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name'):
                vals['name'] = vals['name'].strip()
        return super().create(vals_list)

    def write(self, vals):
        vals = dict(vals)
        if vals.get('name'):
            vals['name'] = vals['name'].strip()
        return super().write(vals)

    @api.model
    def _normalize_city_name(self, name):
        normalized = unicodedata.normalize('NFKD', name or '')
        normalized = ''.join(
            character
            for character in normalized
            if not unicodedata.combining(character)
        )
        normalized = re.sub(r'[^a-z0-9]+', ' ', normalized.casefold())
        return ' '.join(normalized.split())

    @api.model
    def _sync_chilean_city_data(self):
        """Create/update the requested Chilean cities without losing links."""
        country = self.env.ref('base.cl')
        states = self.env['res.country.state'].sudo().search(
            [
                ('country_id', '=', country.id),
                ('code', 'in', list(CHILEAN_CITIES_BY_STATE)),
            ]
        )
        states_by_code = {state.code: state for state in states}
        missing_codes = set(CHILEAN_CITIES_BY_STATE) - set(states_by_code)
        if missing_codes:
            raise ValidationError(
                'No se encontraron las regiones de Chile con código: %s'
                % ', '.join(sorted(missing_codes))
            )

        city_model = self.sudo().with_context(active_test=False)
        employee_model = self.env['hr.employee'].sudo().with_context(
            active_test=False
        )
        existing_cities = city_model.search([])
        cities_by_normalized_name = {}
        for city in existing_cities:
            normalized_name = self._normalize_city_name(city.name)
            cities_by_normalized_name.setdefault(normalized_name, city_model)
            cities_by_normalized_name[normalized_name] |= city

        for state_code, city_names in CHILEAN_CITIES_BY_STATE.items():
            state = states_by_code[state_code]
            for city_name in city_names:
                normalized_name = self._normalize_city_name(city_name)
                candidates = cities_by_normalized_name.get(
                    normalized_name, city_model
                ).exists()

                if candidates:
                    employee_counts = {
                        city.id: employee_model.search_count(
                            [('city_id', '=', city.id)]
                        )
                        for city in candidates
                    }
                    city = candidates.sorted(
                        key=lambda candidate: (
                            -employee_counts[candidate.id],
                            candidate.id,
                        )
                    )[0]
                    duplicates = candidates - city
                    if duplicates:
                        employee_model.search(
                            [('city_id', 'in', duplicates.ids)]
                        ).write({'city_id': city.id})
                        duplicates.unlink()
                else:
                    city = city_model.create(
                        {
                            'name': city_name,
                            'country_id': country.id,
                            'state_id': state.id,
                        }
                    )

                city.write(
                    {
                        'name': city_name,
                        'country_id': country.id,
                        'state_id': state.id,
                        'active': True,
                    }
                )
                cities_by_normalized_name[normalized_name] = city

                matching_employees = employee_model.search(
                    [('private_city', '!=', False)]
                ).filtered(
                    lambda employee: self._normalize_city_name(
                        employee.private_city
                    )
                    == normalized_name
                )
                if matching_employees:
                    matching_employees.write(
                        {
                            'city_id': city.id,
                            'private_country_id': country.id,
                            'private_state_id': state.id,
                        }
                    )
        return True

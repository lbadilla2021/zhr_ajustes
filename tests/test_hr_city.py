from lxml import etree

from odoo.tests.common import TransactionCase

from ..models.hr_city import CHILEAN_CITIES_BY_STATE


class TestHrCity(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.city_model = cls.env['hr.city']
        cls.city_model._sync_chilean_city_data()
        cls.chile = cls.env.ref('base.cl')

    def test_requested_cities_are_linked_to_their_regions(self):
        expected_city_count = sum(
            len(city_names)
            for city_names in CHILEAN_CITIES_BY_STATE.values()
        )
        cities = self.city_model.search(
            [
                ('country_id', '=', self.chile.id),
                ('name', 'in', [
                    city_name
                    for city_names in CHILEAN_CITIES_BY_STATE.values()
                    for city_name in city_names
                ]),
            ]
        )
        self.assertEqual(len(cities), expected_city_count)
        expected_states = {
            city_name: state_code
            for state_code, city_names in CHILEAN_CITIES_BY_STATE.items()
            for city_name in city_names
        }
        for city in cities:
            with self.subTest(city=city.name):
                self.assertEqual(city.state_id.code, expected_states[city.name])

    def test_employee_country_defaults_to_chile(self):
        defaults = self.env['hr.employee'].default_get(['private_country_id'])
        self.assertEqual(defaults['private_country_id'], self.chile.id)

    def test_employee_city_sets_country_region_and_legacy_city_name(self):
        city = self.city_model.search([('name', '=', 'Chillán')], limit=1)
        employee = self.env['hr.employee'].create(
            {
                'name': 'Empleado con ciudad',
                'company_id': self.env.company.id,
                'city_id': city.id,
            }
        )
        self.assertEqual(employee.private_country_id, self.chile)
        self.assertEqual(employee.private_state_id.code, 'CL-NB')
        self.assertEqual(employee.private_city, 'Chillán')

    def test_private_address_keeps_compact_layout_in_requested_order(self):
        arch = self.env['hr.employee'].get_view(view_type='form')['arch']
        document = etree.fromstring(arch)
        address_blocks = document.xpath(
            "//div[contains(concat(' ', normalize-space(@class), ' '), "
            "' o_address_format ')][field[@name='private_country_id']]"
        )
        self.assertEqual(len(address_blocks), 1)
        self.assertTrue(document.xpath("//label[@for='private_street']"))
        self.assertEqual(
            address_blocks[0].xpath('./field/@name'),
            [
                'private_country_id',
                'private_state_id',
                'city_id',
                'private_street',
                'private_street2',
                'private_zip',
            ],
        )
        self.assertEqual(
            address_blocks[0].xpath('./field/@placeholder'),
            ['País', 'Región', 'Ciudad', 'Calle 1...', 'Calle 2...', 'C.P.'],
        )

    def test_sync_reuses_legacy_city_and_preserves_employee_link(self):
        canonical_city = self.city_model.search(
            [('name', '=', 'Cabrero')], limit=1
        )
        legacy_city = self.city_model.create({'name': 'Cabrero.'})
        employee = self.env['hr.employee'].create(
            {
                'name': 'Empleado con ciudad antigua',
                'company_id': self.env.company.id,
                'city_id': legacy_city.id,
            }
        )

        self.city_model._sync_chilean_city_data()

        employee.invalidate_recordset()
        canonical_city.invalidate_recordset()
        matching_cities = self.city_model.search([('name', '=', 'Cabrero')])
        self.assertEqual(len(matching_cities), 1)
        self.assertEqual(employee.city_id, matching_cities)
        self.assertEqual(employee.private_state_id.code, 'CL-BI')
        self.assertFalse(legacy_city.exists() and canonical_city.exists())

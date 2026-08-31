from lxml import etree

from odoo import Command
from odoo.exceptions import AccessError
from odoo.tests.common import TransactionCase


class TestStudyLevel(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.hr_group = cls.env.ref('hr.group_hr_user')
        cls.readonly_group = cls.env.ref(
            'zhr_ajustes.group_zhr_employee_readonly'
        )
        cls.hr_user = cls.env['res.users'].create(
            {
                'name': 'Responsable niveles de estudio',
                'login': 'responsable.niveles.estudio@example.com',
                'groups_id': [Command.set(cls.hr_group.ids)],
            }
        )
        cls.readonly_user = cls.env['res.users'].create(
            {
                'name': 'Consulta niveles de estudio',
                'login': 'consulta.niveles.estudio@example.com',
                'groups_id': [Command.set(cls.readonly_group.ids)],
            }
        )

    def test_initial_catalog(self):
        expected = {
            'SI': 'Sin Escolaridad',
            'BI': 'Básica Incompleta',
            'BC': 'Básica Completa',
            'MI': 'Media Incompleta',
            'MC': 'Media Completa',
            'TPI': 'Técnico Profesional Incompleta',
            'TPC': 'Técnico Profesional Completa',
            'UI': 'Universitaria Incompleta',
            'UC': 'Universitaria Completa',
        }
        levels = self.env['hr.study.level'].with_context(active_test=False).search(
            [('code', 'in', list(expected))]
        )
        self.assertEqual(
            {level.code: level.name for level in levels},
            expected,
        )
        self.assertEqual(
            self.env.ref('zhr_ajustes.hr_study_level_si').display_name,
            'Sin Escolaridad (SI)',
        )

    def test_employee_keeps_standard_certificate_and_new_level(self):
        level = self.env.ref('zhr_ajustes.hr_study_level_uc')
        employee = self.env['hr.employee'].create(
            {
                'name': 'Empleado con nivel de estudio',
                'certificate': 'bachelor',
                'nivel_estudio_id': level.id,
            }
        )
        self.assertEqual(employee.certificate, 'bachelor')
        self.assertEqual(employee.nivel_estudio_id, level)

    def test_employee_form_places_level_after_certificate(self):
        arch = self.env['hr.employee'].get_view(view_type='form')['arch']
        xml = etree.fromstring(arch)
        certificate_nodes = xml.xpath("//field[@name='certificate']")
        self.assertTrue(certificate_nodes)
        following_fields = certificate_nodes[0].xpath(
            "following::field[@name='nivel_estudio_id'][1]"
        )
        self.assertTrue(following_fields)
        self.assertEqual(
            following_fields[0].get('domain'),
            "[('active', '=', True)]",
        )

    def test_hr_user_maintains_catalog_and_readonly_user_only_reads(self):
        level = self.env['hr.study.level'].with_user(self.hr_user).create(
            {'name': 'Nivel de prueba', 'code': ' np '}
        )
        self.assertEqual(level.code, 'NP')
        self.assertEqual(
            level.with_user(self.readonly_user).read(['name'])[0]['name'],
            'Nivel de prueba',
        )
        with self.assertRaises(AccessError):
            level.with_user(self.readonly_user).write({'active': False})

    def test_maintainer_menu_is_under_hr_tables(self):
        menu = self.env.ref('zhr_ajustes.menu_hr_study_level')
        self.assertEqual(menu.parent_id, self.env.ref('zhr_ajustes.menu_hr_tables_root'))
        self.assertEqual(menu.action, self.env.ref('zhr_ajustes.hr_study_level_action'))


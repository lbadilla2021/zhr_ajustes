from lxml import etree

from odoo import Command
from odoo.exceptions import AccessError
from odoo.tests.common import TransactionCase


class TestJobClassification(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.hr_user = cls.env['res.users'].create(
            {
                'name': 'Responsable clasificaciones de cargos',
                'login': 'responsable.clasificaciones.cargos@example.com',
                'groups_id': [Command.set(cls.env.ref('hr.group_hr_user').ids)],
            }
        )
        cls.internal_user = cls.env['res.users'].create(
            {
                'name': 'Consulta clasificaciones de cargos',
                'login': 'consulta.clasificaciones.cargos@example.com',
                'groups_id': [Command.set(cls.env.ref('base.group_user').ids)],
            }
        )

    def test_initial_sence_catalog_and_empty_ine_seed(self):
        expected = {
            '1': 'Empresarios y Ejecutivos',
            '2': 'Profesionales',
            '3': 'Mandos Medios no Profesionales',
            '4': 'Administrativos',
            '5': 'Trabajadores Calificados',
            '6': 'Trabajadores Semicalificados',
            '7': 'Trabajadores no Calificados',
        }
        classifications = self.env[
            'hr.job.sence.classification'
        ].with_context(active_test=False).search([('code', 'in', list(expected))])
        self.assertEqual(
            {
                classification.code: classification.name
                for classification in classifications
            },
            expected,
        )
        self.assertEqual(
            self.env.ref(
                'zhr_ajustes.hr_job_sence_classification_1'
            ).display_name,
            'Empresarios y Ejecutivos (1)',
        )
        ine_seed_data = self.env['ir.model.data'].search(
            [
                ('module', '=', 'zhr_ajustes'),
                ('model', '=', 'hr.job.ine.classification'),
            ]
        )
        self.assertFalse(ine_seed_data)

    def test_job_stores_sence_and_ine_classifications(self):
        sence = self.env.ref('zhr_ajustes.hr_job_sence_classification_2')
        ine = self.env['hr.job.ine.classification'].create(
            {'code': ' ine-1 ', 'name': 'Clasificación INE de prueba'}
        )
        job = self.env['hr.job'].create(
            {
                'name': 'Cargo clasificado',
                'sence_classification_id': sence.id,
                'ine_classification_id': ine.id,
            }
        )
        self.assertEqual(job.sence_classification_id, sence)
        self.assertEqual(job.ine_classification_id, ine)
        self.assertEqual(ine.code, 'INE-1')

    def test_job_views_show_both_columns_and_active_domains(self):
        form_arch = self.env['hr.job'].get_view(view_type='form')['arch']
        list_arch = self.env['hr.job'].get_view(view_type='list')['arch']
        form_xml = etree.fromstring(form_arch)
        list_xml = etree.fromstring(list_arch)
        for field_name in ('sence_classification_id', 'ine_classification_id'):
            with self.subTest(field_name=field_name):
                form_fields = form_xml.xpath(f"//field[@name='{field_name}']")
                list_fields = list_xml.xpath(f"//field[@name='{field_name}']")
                self.assertTrue(form_fields)
                self.assertTrue(list_fields)
                self.assertEqual(
                    form_fields[0].get('domain'),
                    "[('active', '=', True)]",
                )

    def test_catalog_menus_are_under_hr_tables(self):
        root = self.env.ref('zhr_ajustes.menu_hr_tables_root')
        for menu_xmlid in (
            'zhr_ajustes.menu_hr_job_sence_classification',
            'zhr_ajustes.menu_hr_job_ine_classification',
        ):
            with self.subTest(menu_xmlid=menu_xmlid):
                self.assertEqual(self.env.ref(menu_xmlid).parent_id, root)

    def test_hr_user_maintains_catalogs_and_internal_user_only_reads(self):
        ine = self.env['hr.job.ine.classification'].with_user(
            self.hr_user
        ).create({'code': '99', 'name': 'Clasificación INE nueva'})
        values = ine.with_user(self.internal_user).read(['code', 'name'])[0]
        self.assertEqual(values['code'], '99')
        with self.assertRaises(AccessError):
            ine.with_user(self.internal_user).write({'active': False})


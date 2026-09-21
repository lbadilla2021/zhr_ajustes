from datetime import date

from lxml import etree

from odoo.tests.common import TransactionCase


class TestEmploymentCertificate(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.job = cls.env['hr.job'].create({
            'name': 'Cargo Certificado',
            'company_id': cls.env.company.id,
        })
        cls.employee = cls.env['hr.employee'].create({
            'name': 'Empleado Certificado Laboral',
            'company_id': cls.env.company.id,
            'job_id': cls.job.id,
            'fecha_contrato': date(2026, 1, 15),
        })

    def test_employee_form_shows_certificate_button_next_to_termination(self):
        arch = self.env['hr.employee'].get_view(view_type='form')['arch']

        termination_button = 'name="action_open_termination_wizard"'
        certificate_button = 'name="action_print_employment_certificate"'
        self.assertIn(termination_button, arch)
        self.assertIn(certificate_button, arch)
        self.assertLess(arch.index(termination_button), arch.index(certificate_button))

    def test_certificate_button_opens_presentation_place_wizard(self):
        action = self.employee.action_print_employment_certificate()

        self.assertEqual(action['type'], 'ir.actions.act_window')
        self.assertEqual(
            action['res_model'],
            'hr.employee.employment.certificate.wizard',
        )
        self.assertEqual(action['target'], 'new')
        self.assertEqual(action['context']['default_employee_id'], self.employee.id)

    def test_internal_user_can_create_certificate_wizard(self):
        internal_user = self.env['res.users'].create({
            'name': 'Emisor Certificado Interno',
            'login': 'emisor.certificado.interno@example.com',
            'groups_id': [(6, 0, [self.env.ref('base.group_user').id])],
        })

        wizard = self.env[
            'hr.employee.employment.certificate.wizard'
        ].with_user(internal_user).create({
            'employee_id': self.employee.id,
            'presentation_place': 'Institucion de prueba',
        })

        self.assertEqual(wizard.employee_id, self.employee)

    def test_certificate_wizard_passes_presentation_place_by_context(self):
        wizard = self.env[
            'hr.employee.employment.certificate.wizard'
        ].create({
            'employee_id': self.employee.id,
            'presentation_place': 'Banco de Chile',
            'additional_clause': 'Clausula especial del certificado.',
        })

        action = wizard.action_print()

        self.assertEqual(action['type'], 'ir.actions.report')
        self.assertFalse(action['data'])
        self.assertEqual(action['context']['active_ids'], self.employee.ids)
        self.assertEqual(
            action['context']['employment_certificate_presentation_place'],
            'Banco de Chile',
        )
        self.assertEqual(
            action['context']['employment_certificate_additional_clause'],
            'Clausula especial del certificado.',
        )

    def test_certificate_template_has_one_editable_page(self):
        report_view = self.env.ref('zhr_ajustes.report_certificado_laboral')
        report_arch = etree.fromstring(report_view.arch_db.encode())

        self.assertEqual(len(report_arch.xpath("//div[@class='page']")), 1)
        self.assertIn('CERTIFICADO LABORAL', report_view.arch_db)
        self.assertIn('employee.name', report_view.arch_db)
        self.assertIn('employment-certificate-signature', report_view.arch_db)
        self.assertIn('employment-certificate-company-stamp', report_view.arch_db)

    def test_certificate_assets_select_stamp_by_company_name(self):
        signature_uri = self.employee.get_employment_certificate_signature_uri()
        self.assertTrue(signature_uri.startswith('data:image/png;base64,'))

        expected_stamp_prefixes = {
            'Barca SpA': 'data:image/jpeg;base64,',
            'Indoor SpA': 'data:image/jpeg;base64,',
        }
        for company_name, expected_prefix in expected_stamp_prefixes.items():
            self.employee.company_id.name = company_name
            stamp_uri = self.employee.get_employment_certificate_stamp_uri()
            self.assertTrue(stamp_uri.startswith(expected_prefix))

        self.employee.company_id.name = 'Empresa sin timbre'
        self.assertFalse(self.employee.get_employment_certificate_stamp_uri())

    def test_certificate_report_renders_employee_content(self):
        report = self.env.ref('zhr_ajustes.action_report_certificado_laboral')

        html_content, content_type = self.env[
            'ir.actions.report'
        ].with_context(
            employment_certificate_presentation_place='Caja Los Andes',
            employment_certificate_additional_clause=(
                'Clausula adicional de prueba.'
            ),
        )._render_qweb_pdf(report, res_ids=self.employee.ids)

        self.assertEqual(content_type, 'html')
        self.assertIn(b'CERTIFICADO LABORAL', html_content)
        self.assertIn(b'Empleado Certificado Laboral', html_content)
        self.assertIn(b'Cargo Certificado', html_content)
        self.assertIn(b'para ser presentado en', html_content)
        self.assertIn(b'Caja Los Andes', html_content)
        self.assertIn(b'Clausula adicional de prueba.', html_content)
        self.assertIn(b'employment-certificate-signature', html_content)
        self.assertNotIn(b'employment-certificate-company-stamp', html_content)
        self.assertIn(
            b'employment-certificate-additional-clause',
            html_content,
        )
        rendered_text = etree.HTML(html_content).xpath('string()')
        self.assertNotIn('XXX', rendered_text)

    def test_certificate_report_omits_empty_additional_clause(self):
        report = self.env.ref('zhr_ajustes.action_report_certificado_laboral')
        wizard = self.env[
            'hr.employee.employment.certificate.wizard'
        ].create({
            'employee_id': self.employee.id,
            'presentation_place': 'Institucion de prueba',
            'additional_clause': '   ',
        })

        action = wizard.action_print()
        html_content, content_type = self.env[
            'ir.actions.report'
        ].with_context(action['context'])._render_qweb_pdf(
            report,
            res_ids=self.employee.ids,
        )

        self.assertEqual(content_type, 'html')
        self.assertFalse(
            action['context']['employment_certificate_additional_clause']
        )
        self.assertNotIn(
            b'employment-certificate-additional-clause',
            html_content,
        )
        self.assertNotIn(b'AQUI AGREGAR TEXTO', html_content)

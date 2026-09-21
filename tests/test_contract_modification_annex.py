from datetime import date

from lxml import etree

from odoo.tests.common import TransactionCase


class TestContractModificationAnnex(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.company.external_report_layout_id = cls.env.ref(
            'web.external_layout_standard'
        )
        cls.job = cls.env['hr.job'].create({
            'name': 'Supervisor de Operaciones',
            'company_id': cls.env.company.id,
        })
        cls.employee = cls.env['hr.employee'].create({
            'name': 'Empleado Anexo Modificacion',
            'company_id': cls.env.company.id,
            'job_id': cls.job.id,
            'fecha_contrato': date(2026, 1, 15),
        })
        cls.contract = cls.env['hr.contract'].create({
            'name': 'Contrato Anexo Modificacion',
            'employee_id': cls.employee.id,
            'job_id': cls.job.id,
            'date_start': date(2026, 9, 1),
            'wage': 850000,
            'state': 'draft',
        })
        cls.contract.resource_calendar_id.system_schedule = (
            'La jornada será distribuida de lunes a viernes.'
        )
        cls.payment_concept = cls.env['hr.payment.concept'].create({
            'name': 'Bono de produccion',
            'description': 'Bono mensual sujeto al cumplimiento de metas.',
        })
        cls.env['hr.employee.payment.concept'].create({
            'contract_id': cls.contract.id,
            'payment_concept_id': cls.payment_concept.id,
            'amount': 75000,
        })

    def _create_wizard(self, **values):
        wizard_values = {
            'contract_id': self.contract.id,
            'report_type': 'modificacion',
            'show_sueldo_base': True,
            'show_cargo_actual': True,
            'show_jornada_trabajo': True,
            'show_payment_concepts': True,
        }
        wizard_values.update(values)
        return self.env['hr.contract.actualizacion.wizard'].create(
            wizard_values
        )

    def test_modification_type_enables_all_content_options(self):
        wizard = self._create_wizard(
            show_sueldo_base=False,
            show_cargo_actual=False,
            show_jornada_trabajo=False,
            show_payment_concepts=False,
        )

        wizard._onchange_report_type()

        self.assertTrue(wizard.show_sueldo_base)
        self.assertTrue(wizard.show_cargo_actual)
        self.assertTrue(wizard.show_jornada_trabajo)
        self.assertTrue(wizard.show_payment_concepts)

    def test_modification_action_uses_its_own_report(self):
        action = self._create_wizard().action_confirm()

        self.assertEqual(
            action['report_name'],
            'zhr_ajustes.report_modificacion',
        )

    def test_modification_report_renders_payment_concepts(self):
        wizard = self._create_wizard()
        report = self.env.ref('zhr_ajustes.action_report_modificacion')

        html_content, content_type = self.env[
            'ir.actions.report'
        ]._render_qweb_html(report, wizard.ids)
        rendered_text = ' '.join(
            etree.HTML(html_content).xpath('string()').split()
        )

        self.assertEqual(content_type, 'html')
        self.assertIn('ANEXO MODIFICACIÓN', rendered_text)
        self.assertIn('A partir de 1 de septiembre de 2026', rendered_text)
        self.assertIn('Sueldo base', rendered_text)
        self.assertIn('Cargo', rendered_text)
        self.assertIn('Jornada de Trabajo', rendered_text)
        self.assertIn(
            'La jornada es distribuida de lunes a viernes.',
            rendered_text,
        )
        self.assertNotIn('La jornada será', rendered_text)
        self.assertIn('Beneficios', rendered_text)
        self.assertIn('Bono de produccion', rendered_text)
        self.assertIn(
            'Bono mensual sujeto al cumplimiento de metas.',
            rendered_text,
        )

    def test_modification_report_omits_unselected_payment_concepts(self):
        wizard = self._create_wizard(show_payment_concepts=False)
        report = self.env.ref('zhr_ajustes.action_report_modificacion')

        html_content, _content_type = self.env[
            'ir.actions.report'
        ]._render_qweb_html(report, wizard.ids)
        rendered_text = etree.HTML(html_content).xpath('string()')

        self.assertNotIn('Bono de produccion', rendered_text)

    def test_mass_print_creates_modification_wizard(self):
        mass_wizard = self.env['hr.contract.mass.print.wizard'].create({
            'contract_ids': [(6, 0, self.contract.ids)],
            'actualizacion_report_type': 'modificacion',
            'show_sueldo_base': True,
            'show_cargo_actual': True,
            'show_jornada_trabajo': True,
            'show_payment_concepts': True,
        })

        report_xml_id, wizard = mass_wizard._get_report_record(
            'actualizacion',
            self.contract,
        )

        self.assertEqual(
            report_xml_id,
            'zhr_ajustes.action_report_modificacion',
        )
        self.assertEqual(wizard.report_type, 'modificacion')
        self.assertTrue(wizard.show_payment_concepts)

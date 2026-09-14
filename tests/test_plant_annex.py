from datetime import date

from lxml import etree

from odoo.tests.common import TransactionCase


class TestPlantAnnex(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.employee = cls.env['hr.employee'].create({
            'name': 'Empleado Anexo Planta',
            'company_id': cls.env.company.id,
        })
        cls.contract = cls.env['hr.contract'].create({
            'name': 'Contrato Anexo Planta',
            'employee_id': cls.employee.id,
            'date_start': date(2026, 1, 1),
            'wage': 1000,
            'state': 'draft',
        })
        cls.arauco = cls.env.ref('zhr_ajustes.hr_plant_annex_client_arauco')
        cls.cmpc = cls.env.ref('zhr_ajustes.hr_plant_annex_client_cmpc')

    def test_default_clients_have_editable_html_clauses(self):
        self.assertEqual(self.arauco.name, 'Arauco')
        self.assertEqual(self.cmpc.name, 'CMPC')
        self.assertIn('<li>', self.arauco.clause_html)
        self.assertIn('CELULOSA ARAUCO LOS HORCONES', self.arauco.clause_html)
        self.assertIn('<li>', self.cmpc.clause_html)
        self.assertIn('CMPC PULP PLANTA LAJA', self.cmpc.clause_html)

        self.cmpc.write({'clause_html': '<ul><li>Clausula modificada</li></ul>'})

        self.assertIn('Clausula modificada', self.cmpc.clause_html)

    def test_contract_button_opens_client_selection_wizard(self):
        action = self.contract.action_print_anexo_planta()

        self.assertEqual(action['res_model'], 'hr.contract.plant.annex.wizard')
        self.assertEqual(action['context']['default_contract_id'], self.contract.id)

    def test_wizard_passes_selected_client_to_report_context(self):
        wizard = self.env['hr.contract.plant.annex.wizard'].create({
            'contract_id': self.contract.id,
            'client_id': self.arauco.id,
        })

        action = wizard.action_print()

        self.assertFalse(action['data'])
        self.assertEqual(
            action['context']['plant_annex_client_id'],
            self.arauco.id,
        )

    def test_web_report_action_keeps_docids_and_contract_content(self):
        wizard = self.env['hr.contract.plant.annex.wizard'].create({
            'contract_id': self.contract.id,
            'client_id': self.cmpc.id,
        })
        action = wizard.action_print()
        report = self.env.ref('zhr_ajustes.action_report_anexo_planta')

        # The selected client travels in the context so the web client keeps
        # the contract IDs in the report URL. Sending it through ``data``
        # would omit docids and wkhtmltopdf would generate a blank page.
        html_content, content_type = self.env[
            'ir.actions.report'
        ].with_context(action['context'])._render_qweb_html(
            report,
            self.contract.ids,
            data=action['data'],
        )

        self.assertEqual(content_type, 'html')
        self.assertIn(b'Empleado Anexo Planta', html_content)
        self.assertIn(b'CMPC PULP PLANTA LAJA', html_content)

    def test_report_uses_one_page_and_dynamic_clause(self):
        report_values = self.env[
            'report.zhr_ajustes.report_anexo_planta'
        ]._get_report_values(
            self.contract.ids,
            data={'plant_annex_client_id': self.arauco.id},
        )
        report_view = self.env.ref('zhr_ajustes.report_anexo_planta')
        report_arch = etree.fromstring(report_view.arch_db.encode())

        self.assertEqual(report_values['plant_annex_client'], self.arauco)
        self.assertEqual(len(report_arch.xpath("//div[@class='page']")), 1)
        self.assertTrue(
            report_arch.xpath(
                "//div[@t-field='plant_annex_client.clause_html']"
            )
        )
        self.assertNotIn('CELULOSA ARAUCO LOS HORCONES', report_view.arch_db)
        self.assertNotIn('CMPC PULP PLANTA LAJA', report_view.arch_db)

    def test_report_renders_selected_client_clause(self):
        report = self.env.ref('zhr_ajustes.action_report_anexo_planta')

        html_content, content_type = self.env['ir.actions.report']._render_qweb_pdf(
            report,
            res_ids=self.contract.ids,
            data={'plant_annex_client_id': self.cmpc.id},
        )

        # Odoo intentionally returns HTML while tests are enabled; outside test
        # mode the same render path converts this content to PDF.
        self.assertEqual(content_type, 'html')
        self.assertIn(b'CMPC PULP PLANTA LAJA', html_content)
        self.assertNotIn(b'CELULOSA ARAUCO LOS HORCONES', html_content)

    def test_mass_print_requests_plant_annex_client(self):
        wizard = self.env['hr.contract.mass.print.wizard'].create({
            'contract_ids': [(6, 0, self.contract.ids)],
        })

        action = wizard.action_print_anexo_planta()

        self.assertTrue(wizard.show_plant_annex_options)
        self.assertEqual(action['res_id'], wizard.id)

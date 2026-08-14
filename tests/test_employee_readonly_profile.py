from datetime import date

from odoo.exceptions import AccessError, ValidationError
from odoo.tests.common import TransactionCase


class TestEmployeeReadonlyProfile(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group_readonly = cls.env.ref(
            "zhr_ajustes.group_zhr_employee_readonly"
        )
        cls.viewer_user = cls.env["res.users"].create(
            {
                "name": "Consulta Empleados",
                "login": "consulta.empleados@example.com",
                "groups_id": [(6, 0, [cls.group_readonly.id])],
            }
        )
        cls.employee = cls.env["hr.employee"].create(
            {
                "name": "Empleado Consulta",
                "nombres": "Empleado",
                "apellido_paterno": "Consulta",
                "identification_id": "12345678",
                "rut_dv": "5",
                "company_id": cls.env.company.id,
            }
        )

    def test_readonly_group_does_not_imply_hr_employee_officer(self):
        self.assertFalse(self.viewer_user.has_group("hr.group_hr_user"))

    def test_readonly_group_can_read_private_employee_fields(self):
        employee = self.employee.with_user(self.viewer_user)
        readable_fields = ["nombres", "apellido_paterno", "rut_dv"]
        for field_name in ("current_leave_id", "activity_ids"):
            if field_name in employee._fields:
                readable_fields.append(field_name)
        values = employee.read(readable_fields)[0]
        self.assertEqual(values["nombres"], "Empleado")
        self.assertEqual(values["rut_dv"], "5")

    def test_readonly_user_cannot_create_write_or_delete_employee(self):
        employee_model = self.env["hr.employee"].with_user(self.viewer_user)
        with self.assertRaises(AccessError):
            employee_model.create({"name": "Intento"})
        with self.assertRaises(AccessError):
            self.employee.with_user(self.viewer_user).write({"name": "Intento"})
        with self.assertRaises(AccessError):
            self.employee.with_user(self.viewer_user).unlink()

    def test_readonly_group_menu_visibility(self):
        employee_menu = self.env.ref("hr.menu_hr_employee_payroll")
        self.assertIn(self.group_readonly, employee_menu.groups_id)

        hidden_menu_xmlids = [
            "hr_contract.hr_menu_contract",
            "hr_contract.menu_hr_employee_contracts",
            "zhr_ajustes.menu_hr_tables_root",
        ]
        for menu_xmlid in hidden_menu_xmlids:
            with self.subTest(menu_xmlid=menu_xmlid):
                menu = self.env.ref(menu_xmlid)
                self.assertNotIn(self.group_readonly, menu.groups_id)

    def test_readonly_user_cannot_access_contracts(self):
        restricted_models = [
            "hr.contract",
            "hr.contract.history",
        ]
        for model_name in restricted_models:
            with self.subTest(model_name=model_name):
                with self.assertRaises(AccessError):
                    self.env[model_name].with_user(self.viewer_user).search([], limit=1)

    def test_readonly_employee_form_shows_private_info(self):
        arch = self.env["hr.employee"].with_user(self.viewer_user).get_view(
            view_type="form"
        )["arch"]
        self.assertIn('name="personal_information"', arch)
        self.assertIn('name="hide_resume_for_readonly"', arch)
        self.assertIn('name="skills_resume"', arch)
        self.assertIn('invisible="hide_resume_for_readonly"', arch)

    def test_employee_form_shows_first_entry_date(self):
        arch = self.env["hr.employee"].get_view(view_type="form")["arch"]
        self.assertIn('name="fecha_contrato"', arch)
        self.assertIn('name="fecha_finiquito"', arch)
        self.assertIn('name="fecha_primer_ingreso"', arch)
        self.assertIn('name="fecha_contrato" readonly="1"', arch)
        self.assertIn('name="fecha_finiquito" readonly="1"', arch)
        self.assertIn('name="fecha_primer_ingreso" string="Fecha primer ingreso" readonly="1"', arch)
        self.assertNotIn('name="first_contract_date" string="Fecha de Ingreso"', arch)
        self.assertNotIn('name="departure_date" string="Fecha de Salida"', arch)
        self.assertLess(
            arch.index('name="fecha_finiquito"'),
            arch.index('name="fecha_primer_ingreso"'),
        )

    def test_contract_state_has_expired_history_label(self):
        selection = self.env["hr.contract"].fields_get(["state"], ["selection"])[
            "state"
        ]["selection"]
        labels = dict(selection)
        self.assertIn("close", labels)
        self.assertEqual(labels["expired"], "Expirado")
        state_order = [value for value, label in selection]
        self.assertLess(state_order.index("draft"), state_order.index("open"))
        self.assertLess(state_order.index("open"), state_order.index("close"))
        self.assertLess(state_order.index("close"), state_order.index("expired"))
        self.assertLess(state_order.index("expired"), state_order.index("cancel"))

    def test_contract_form_shows_contract_dates_and_icon_only_duplicate_button(self):
        arch = self.env["hr.contract"].get_view(view_type="form")["arch"]
        self.assertIn('name="reference_id"', arch)
        self.assertIn('options="{\'no_create\': True, \'no_create_edit\': True}"', arch)
        self.assertIn('readonly="1"', arch)
        self.assertIn('name="fecha_contrato"', arch)
        self.assertIn('name="fecha_finiquito"', arch)
        self.assertIn('name="departure_reason_id"', arch)
        self.assertIn('invisible="not fecha_finiquito"', arch)
        self.assertNotIn('name="contract_gap_start"', arch)
        self.assertNotIn('name="contract_gap_end"', arch)
        self.assertNotIn('name="contract_gap_reason"', arch)
        self.assertIn('statusbar_visible="draft,open,close,expired,cancel"', arch)
        self.assertIn("statusbar_colors=\"{'expired': 'gray', 'cancel': 'gray'}\"", arch)
        self.assertIn('string="Fecha inicio de vigencia"', arch)
        self.assertIn('string="Fecha de finalización vigencia"', arch)
        self.assertLess(
            arch.index('name="reference_id"'),
            arch.index('name="fecha_contrato"'),
        )
        self.assertLess(
            arch.index('name="fecha_contrato"'),
            arch.index('name="fecha_finiquito"'),
        )
        self.assertLess(
            arch.index('name="fecha_finiquito"'),
            arch.index('name="date_start"'),
        )
        self.assertLess(
            arch.index('name="contract_type_id"'),
            arch.index('name="departure_reason_id"'),
        )
        self.assertLess(
            arch.index('name="departure_reason_id"'),
            arch.index('name="tipo_obra_id"'),
        )
        self.assertIn('name="action_open_duplicate_wizard"', arch)
        self.assertNotIn('name="action_open_duplicate_wizard" type="object" string="+"', arch)
        self.assertIn('name="wage"', arch)
        self.assertIn('required="1"', arch)
        self.assertIn('name="wage_positive_check"', arch)
        self.assertIn('required="wage &lt;= 0"', arch)
        self.assertIn('invisible="wage &gt; 0"', arch)
        self.assertNotIn('name="show_wage_warning"', arch)
        self.assertNotIn('alert alert-warning', arch)

    def test_contract_list_shows_all_contract_dates(self):
        arch = self.env["hr.contract"].get_view(view_type="list")["arch"]
        self.assertIn('name="fecha_contrato"', arch)
        self.assertIn('name="date_start"', arch)
        self.assertIn('string="Fecha inicio de vigencia"', arch)
        self.assertIn('name="date_end"', arch)
        self.assertIn('string="Fecha de finalización vigencia"', arch)
        self.assertIn('name="fecha_finiquito"', arch)
        self.assertIn('decoration-warning="state == \'close\'"', arch)
        self.assertIn('decoration-muted="state == \'expired\' or state == \'cancel\'"', arch)
        self.assertNotIn('decoration-danger="state == \'cancel\'"', arch)
        self.assertLess(
            arch.index('name="fecha_contrato"'),
            arch.index('name="fecha_finiquito"'),
        )
        self.assertLess(
            arch.index('name="fecha_finiquito"'),
            arch.index('name="date_start"'),
        )
        self.assertLess(
            arch.index('name="date_start"'),
            arch.index('name="date_end"'),
        )

    def test_custom_contract_fields_have_tooltip_help(self):
        fields_info = self.env["hr.contract"].fields_get(
            [
                "fecha_contrato",
                "fecha_finiquito",
                "reference_id",
                "tipo_obra_id",
                "duracion_obra",
                "lugar_trabajo_id",
                "departure_reason_id",
            ],
            ["help"],
        )
        for field_name, field_info in fields_info.items():
            with self.subTest(field_name=field_name):
                self.assertTrue(field_info["help"])

    def test_contract_wage_must_be_positive(self):
        for wage in (0, -1):
            with self.subTest(wage=wage):
                with self.assertRaisesRegex(ValidationError, "salario.*mayor a 0"):
                    with self.env.cr.savepoint():
                        self.env["hr.contract"].create(
                            {
                                "name": "Contrato salario invalido",
                                "employee_id": self.employee.id,
                                "date_start": date(2026, 1, 1),
                                "wage": wage,
                            }
                        )

        contract = self.env["hr.contract"].create(
            {
                "name": "Contrato salario valido",
                "employee_id": self.employee.id,
                "date_start": date(2026, 1, 1),
                "wage": 1000,
            }
        )
        self.assertEqual(contract.wage_positive_check, "ok")
        with self.assertRaisesRegex(ValidationError, "salario.*mayor a 0"):
            with self.env.cr.savepoint():
                contract.write({"wage": 0})

    def test_contract_date_is_independent_from_employee_first_entry_date(self):
        self.employee.fecha_primer_ingreso = date(2025, 5, 10)
        contract = self.env["hr.contract"].create(
            {
                "name": "Contrato con fecha asociada",
                "employee_id": self.employee.id,
                "date_start": date(2026, 1, 1),
                "fecha_contrato": date(2026, 1, 5),
                "wage": 1000,
            }
        )

        self.assertEqual(contract.fecha_contrato, date(2026, 1, 5))
        contract.fecha_contrato = date(2025, 6, 1)
        self.assertEqual(contract.fecha_contrato, date(2025, 6, 1))
        self.assertEqual(contract.date_start, date(2026, 1, 1))
        self.assertEqual(self.employee.fecha_primer_ingreso, date(2025, 5, 10))

    def test_contract_reference_date_overrides_stale_employee_date(self):
        contract_reference = self.env.ref(
            "zhr_ajustes.hr_contract_reference_contract"
        )
        self.employee.fecha_contrato = date(2020, 1, 1)
        contract = self.env["hr.contract"].create(
            {
                "name": "Contrato corregido",
                "employee_id": self.employee.id,
                "reference_id": contract_reference.id,
                "fecha_contrato": date(2026, 1, 5),
                "date_start": date(2026, 1, 10),
                "wage": 1000,
                "state": "open",
            }
        )

        self.assertTrue(contract.can_edit_fecha_contrato)
        self.assertEqual(contract.fecha_contrato, date(2026, 1, 5))
        contract.write({"fecha_contrato": date(2026, 1, 7)})
        self.assertEqual(contract.fecha_contrato, date(2026, 1, 7))
        self.assertEqual(contract.date_start, date(2026, 1, 10))
        self.assertEqual(self.employee.fecha_contrato, date(2026, 1, 7))

    def test_legacy_contract_becomes_editable_with_contract_reference(self):
        employee = self.env["hr.employee"].create(
            {
                "name": "Empleado Contratos Migrados",
                "company_id": self.env.company.id,
            }
        )
        self.env["hr.contract"].create(
            {
                "name": "Contrato historico",
                "employee_id": employee.id,
                "fecha_contrato": date(2020, 1, 1),
                "date_start": date(2020, 1, 1),
                "date_end": date(2020, 12, 31),
                "wage": 1000,
                "state": "expired",
            }
        )
        legacy_contract = self.env["hr.contract"].create(
            {
                "name": "Contrato migrado",
                "employee_id": employee.id,
                "fecha_contrato": date(2021, 1, 1),
                "date_start": date(2021, 1, 1),
                "wage": 1000,
                "state": "open",
            }
        )

        self.assertFalse(legacy_contract.can_edit_fecha_contrato)
        legacy_contract.reference_id = self.env.ref(
            "zhr_ajustes.hr_contract_reference_contract"
        )
        self.assertTrue(legacy_contract.can_edit_fecha_contrato)
        legacy_contract.fecha_contrato = date(2021, 1, 15)
        self.assertEqual(legacy_contract.fecha_contrato, date(2021, 1, 15))
        self.assertEqual(legacy_contract.date_start, date(2021, 1, 1))

    def test_schedule_details_are_multiline_text_fields(self):
        self.assertEqual(
            self.env["resource.calendar"]._fields["system_schedule"].type,
            "text",
        )
        self.assertEqual(
            self.env["hr.contract"]._fields["schedule_details"].type,
            "text",
        )
        arch = self.env["resource.calendar"].get_view(view_type="form")["arch"]
        self.assertIn('name="system_schedule"', arch)
        self.assertIn('colspan="2"', arch)
        self.assertIn('placeholder="Describa el horario de trabajo..."', arch)

    def test_driver_license_accreditation_has_configured_types(self):
        license_type = self.env.ref(
            "zhr_ajustes.hr_accreditation_type_driver_license"
        )
        self.assertEqual(
            set(license_type.subtype_ids.mapped("name")),
            {"A1", "A2", "A3", "A4", "A5", "B", "C", "CR", "D", "E", "F"},
        )

    def test_accreditation_subtype_has_searchable_description(self):
        subtype_model = self.env["hr.accreditation.subtype"]
        self.assertEqual(subtype_model._fields["description"].type, "char")
        self.assertIn("description", subtype_model._rec_names_search)

        view = self.env.ref("zhr_ajustes.hr_accreditation_type_form_view")
        self.assertIn('name="description"', view.arch_db)

    def test_employee_accreditation_accepts_multiple_matching_types(self):
        license_type = self.env.ref(
            "zhr_ajustes.hr_accreditation_type_driver_license"
        )
        selected_types = license_type.subtype_ids.filtered(
            lambda subtype: subtype.name in {"A1", "B", "CR"}
        )
        accreditation = self.env["hr.employee.accreditation"].create(
            {
                "employee_id": self.employee.id,
                "accreditation_type_id": license_type.id,
                "accreditation_subtype_ids": [(6, 0, selected_types.ids)],
            }
        )

        self.assertEqual(
            set(accreditation.accreditation_subtype_ids.mapped("name")),
            {"A1", "B", "CR"},
        )

    def test_employee_accreditation_rejects_type_from_another_category(self):
        license_type = self.env.ref(
            "zhr_ajustes.hr_accreditation_type_driver_license"
        )
        other_category = self.env["hr.accreditation.type"].create(
            {"name": "Certificación técnica"}
        )
        other_subtype = self.env["hr.accreditation.subtype"].create(
            {
                "name": "Nivel 1",
                "accreditation_type_id": other_category.id,
            }
        )

        with self.assertRaisesRegex(ValidationError, "deben pertenecer"):
            self.env["hr.employee.accreditation"].create(
                {
                    "employee_id": self.employee.id,
                    "accreditation_type_id": license_type.id,
                    "accreditation_subtype_ids": [(6, 0, other_subtype.ids)],
                }
            )

    def test_employee_accreditation_view_uses_filtered_multiselect(self):
        arch = self.env["hr.employee"].get_view(view_type="form")["arch"]
        self.assertIn('name="accreditation_subtype_ids"', arch)
        self.assertIn('widget="many2many_tags"', arch)
        self.assertIn(
            "('accreditation_type_id', '=', accreditation_type_id)",
            arch,
        )

    def test_contract_reference_selector_updates_contract_name(self):
        reference = self.env.ref("zhr_ajustes.hr_contract_reference_annex_job")
        contract = self.env["hr.contract"].create(
            {
                "name": "Temporal",
                "employee_id": self.employee.id,
                "reference_id": reference.id,
                "date_start": date(2026, 1, 1),
                "wage": 1000,
            }
        )

        self.assertEqual(contract.name, "Anexo Cargo - Empleado Consulta")

    def test_new_contract_reference_uses_explicit_contract_date(self):
        contract_reference = self.env.ref("zhr_ajustes.hr_contract_reference_contract")
        employee = self.env["hr.employee"].create(
            {
                "name": "Empleado Fecha Contrato",
                "company_id": self.env.company.id,
            }
        )
        self.env["hr.contract"].create(
            {
                "name": "Primer contrato",
                "employee_id": employee.id,
                "reference_id": contract_reference.id,
                "fecha_contrato": date(2026, 1, 1),
                "date_start": date(2026, 1, 1),
                "date_end": date(2026, 1, 31),
                "wage": 1000,
                "state": "expired",
            }
        )
        new_contract = self.env["hr.contract"].create(
            {
                "name": "Segundo contrato",
                "employee_id": employee.id,
                "reference_id": contract_reference.id,
                "fecha_contrato": date(2026, 2, 1),
                "date_start": date(2026, 2, 1),
                "wage": 1200,
                "state": "open",
            }
        )

        self.assertEqual(new_contract.fecha_contrato, date(2026, 2, 1))
        self.assertEqual(new_contract.date_start, date(2026, 2, 1))

    def test_open_contract_syncs_employee_work_dates(self):
        employee = self.env["hr.employee"].create(
            {
                "name": "Empleado Fechas",
                "company_id": self.env.company.id,
            }
        )
        self.env["hr.contract"].create(
            {
                "name": "Contrato anterior",
                "employee_id": employee.id,
                "date_start": date(2026, 1, 10),
                "date_end": date(2026, 2, 24),
                "wage": 1000,
                "state": "expired",
            }
        )
        contract = self.env["hr.contract"].create(
            {
                "name": "Contrato vigente",
                "employee_id": employee.id,
                "date_start": date(2026, 3, 1),
                "fecha_contrato": date(2026, 2, 25),
                "fecha_finiquito": date(2026, 12, 31),
                "wage": 1200,
                "state": "open",
            }
        )

        self.assertEqual(employee.fecha_contrato, date(2026, 2, 25))
        self.assertEqual(employee.fecha_finiquito, date(2026, 12, 31))
        self.assertEqual(employee.fecha_primer_ingreso, date(2026, 1, 10))
        self.assertEqual(contract.date_start, date(2026, 2, 25))
        self.assertEqual(contract.date_end, date(2026, 12, 31))

        contract.write({"fecha_finiquito": date(2027, 1, 15)})

        self.assertEqual(contract.date_end, date(2027, 1, 15))
        self.assertEqual(employee.fecha_finiquito, date(2027, 1, 15))
        self.assertEqual(employee.fecha_primer_ingreso, date(2026, 1, 10))

    def test_contract_dates_autocomplete_from_custom_dates(self):
        contract = self.env["hr.contract"].create(
            {
                "name": "Contrato con fechas automaticas",
                "employee_id": self.employee.id,
                "fecha_contrato": date(2026, 4, 1),
                "fecha_finiquito": date(2026, 4, 30),
                "wage": 1000,
                "state": "draft",
            }
        )

        self.assertEqual(contract.date_start, date(2026, 4, 1))
        self.assertEqual(contract.date_end, date(2026, 4, 30))

    def test_future_end_date_sets_contract_open_on_save(self):
        contract = self.env["hr.contract"].create(
            {
                "name": "Contrato vencido corregido",
                "employee_id": self.employee.id,
                "date_start": date(2026, 1, 1),
                "date_end": date(2026, 7, 1),
                "wage": 1000,
                "state": "close",
            }
        )

        contract.write({"date_end": date(2026, 7, 29)})

        self.assertEqual(contract.state, "open")

    def test_new_real_contract_closes_previous_open_contract(self):
        employee = self.env["hr.employee"].create(
            {
                "name": "Empleado Continuidad",
                "company_id": self.env.company.id,
            }
        )
        previous_contract = self.env["hr.contract"].create(
            {
                "name": "Contrato vigente anterior",
                "employee_id": employee.id,
                "date_start": date(2026, 1, 1),
                "wage": 1000,
                "state": "open",
            }
        )

        self.env["hr.contract"].with_context(close_previous_contract=True).create(
            {
                "name": "Contrato nuevo",
                "employee_id": employee.id,
                "date_start": date(2026, 2, 1),
                "wage": 1200,
                "state": "open",
            }
        )

        self.assertEqual(previous_contract.state, "expired")
        self.assertEqual(previous_contract.date_end, date(2026, 1, 31))

    def test_manual_draft_contract_does_not_expire_current_open_contract(self):
        employee = self.env["hr.employee"].create(
            {
                "name": "Empleado Borrador Manual",
                "company_id": self.env.company.id,
            }
        )
        previous_contract = self.env["hr.contract"].create(
            {
                "name": "Contrato vigente",
                "employee_id": employee.id,
                "date_start": date(2026, 1, 1),
                "wage": 1000,
                "state": "open",
            }
        )

        new_contract = self.env["hr.contract"].create(
            {
                "name": "Contrato nuevo en borrador",
                "employee_id": employee.id,
                "date_start": date(2026, 2, 1),
                "wage": 1200,
            }
        )

        self.assertEqual(previous_contract.state, "open")
        self.assertEqual(new_contract.state, "open")

    def test_deleting_contracts_clears_employee_work_dates(self):
        employee = self.env["hr.employee"].create(
            {
                "name": "Empleado Limpieza Fechas",
                "company_id": self.env.company.id,
            }
        )
        contract = self.env["hr.contract"].create(
            {
                "name": "Contrato vigente",
                "employee_id": employee.id,
                "date_start": date(2026, 1, 1),
                "fecha_contrato": date(2026, 1, 1),
                "fecha_finiquito": date(2026, 7, 31),
                "wage": 1000,
                "state": "open",
            }
        )

        self.assertEqual(employee.fecha_contrato, date(2026, 1, 1))
        self.assertEqual(employee.fecha_finiquito, date(2026, 7, 31))

        contract.unlink()

        self.assertFalse(employee.fecha_contrato)
        self.assertFalse(employee.fecha_finiquito)
        self.assertFalse(employee.fecha_primer_ingreso)

    def test_contract_gap_is_blocked_between_real_contracts(self):
        employee = self.env["hr.employee"].create(
            {
                "name": "Empleado Vacio",
                "company_id": self.env.company.id,
            }
        )
        self.env["hr.contract"].create(
            {
                "name": "Contrato anterior",
                "employee_id": employee.id,
                "date_start": date(2026, 1, 1),
                "date_end": date(2026, 1, 31),
                "wage": 1000,
                "state": "expired",
            }
        )

        with self.assertRaisesRegex(ValidationError, "vacio contractual"):
            self.env["hr.contract"].create(
                {
                    "name": "Contrato con vacio",
                    "employee_id": employee.id,
                    "date_start": date(2026, 2, 10),
                    "wage": 1200,
                    "state": "open",
                }
            )

    def test_cancelled_contract_allows_gap_or_overlap(self):
        employee = self.env["hr.employee"].create(
            {
                "name": "Empleado Cancelado",
                "company_id": self.env.company.id,
            }
        )
        previous_contract = self.env["hr.contract"].create(
            {
                "name": "Contrato vigente",
                "employee_id": employee.id,
                "date_start": date(2026, 1, 1),
                "wage": 1000,
                "state": "open",
            }
        )

        cancelled_contract = self.env["hr.contract"].create(
            {
                "name": "Contrato terminado",
                "employee_id": employee.id,
                "date_start": date(2026, 1, 15),
                "date_end": date(2026, 1, 20),
                "wage": 1200,
                "state": "cancel",
            }
        )

        self.assertEqual(cancelled_contract.state, "cancel")
        self.assertEqual(previous_contract.state, "open")

    def test_termination_wizard_sets_departure_cancels_contracts_and_archives(self):
        reason = self.env["hr.departure.reason"].create({"name": "Renuncia"})
        first_contract = self.env["hr.contract"].create(
            {
                "name": "Contrato plazo fijo",
                "employee_id": self.employee.id,
                "date_start": date(2026, 1, 1),
                "fecha_contrato": date(2026, 1, 1),
                "wage": 1000,
                "state": "open",
            }
        )
        second_contract = self.env["hr.contract"].create(
            {
                "name": "Contrato indefinido",
                "employee_id": self.employee.id,
                "date_start": date(2026, 3, 1),
                "date_end": date(2026, 6, 30),
                "wage": 1200,
                "state": "expired",
            }
        )
        draft_contract = self.env["hr.contract"].create(
            {
                "name": "Contrato borrador",
                "employee_id": self.employee.id,
                "date_start": date(2026, 8, 1),
                "wage": 1300,
                "state": "draft",
            }
        )
        wizard = self.env["hr.employee.termination.wizard"].create(
            {
                "employee_id": self.employee.id,
                "departure_reason_id": reason.id,
                "departure_date": date(2026, 7, 24),
            }
        )

        wizard.action_confirm()

        self.assertFalse(self.employee.active)
        self.assertEqual(self.employee.state, "inactive")
        self.assertEqual(self.employee.departure_reason_id, reason)
        self.assertEqual(self.employee.departure_date, date(2026, 7, 24))
        self.assertEqual(self.employee.fecha_finiquito, date(2026, 7, 24))
        self.assertEqual(first_contract.state, "cancel")
        self.assertEqual(first_contract.date_end, date(2026, 7, 24))
        self.assertEqual(first_contract.fecha_finiquito, date(2026, 7, 24))
        self.assertEqual(first_contract.departure_reason_id, reason)
        self.assertEqual(second_contract.state, "cancel")
        self.assertEqual(second_contract.date_end, date(2026, 7, 24))
        self.assertEqual(second_contract.fecha_finiquito, date(2026, 7, 24))
        self.assertEqual(second_contract.departure_reason_id, reason)
        self.assertEqual(draft_contract.state, "cancel")
        self.assertEqual(draft_contract.fecha_finiquito, date(2026, 7, 24))
        self.assertEqual(draft_contract.departure_reason_id, reason)
        settlement_contract = self.env["hr.contract"].search(
            [
                ("employee_id", "=", self.employee.id),
                (
                    "reference_id",
                    "=",
                    self.env.ref("zhr_ajustes.hr_contract_reference_settlement").id,
                ),
            ],
            limit=1,
        )
        self.assertEqual(settlement_contract.name, "Finiquito - Empleado Consulta")
        self.assertEqual(settlement_contract.fecha_contrato, date(2026, 1, 1))
        self.assertEqual(settlement_contract.date_start, date(2026, 7, 24))
        self.assertEqual(settlement_contract.date_end, date(2026, 7, 24))
        self.assertEqual(settlement_contract.fecha_finiquito, date(2026, 7, 24))
        self.assertEqual(settlement_contract.departure_reason_id, reason)
        self.assertEqual(settlement_contract.state, "cancel")

    def test_reactivation_wizard_unarchives_employee(self):
        reason = self.env["hr.departure.reason"].create({"name": "Renuncia"})
        previous_contract = self.env["hr.contract"].create(
            {
                "name": "Contrato anterior",
                "employee_id": self.employee.id,
                "date_start": date(2026, 1, 1),
                "date_end": date(2026, 7, 24),
                "fecha_finiquito": date(2026, 7, 24),
                "departure_reason_id": reason.id,
                "wage": 1000,
                "state": "cancel",
            }
        )
        pending_contract = self.env["hr.contract"].create(
            {
                "name": "Contrato pendiente",
                "employee_id": self.employee.id,
                "date_start": date(2026, 7, 25),
                "wage": 1200,
                "state": "open",
            }
        )
        self.employee.write({
            "active": False,
            "state": "inactive",
            "fecha_primer_ingreso": date(2026, 1, 1),
        })
        wizard = self.env["hr.employee.reactivation.wizard"].create(
            {
                "employee_id": self.employee.id,
                "fecha_contrato": date(2026, 8, 1),
            }
        )

        wizard.action_confirm()

        self.assertTrue(self.employee.active)
        self.assertEqual(self.employee.state, "active")
        self.assertEqual(self.employee.fecha_contrato, date(2026, 8, 1))
        self.assertEqual(self.employee.fecha_primer_ingreso, date(2026, 1, 1))
        self.assertFalse(self.employee.fecha_finiquito)
        self.assertEqual(previous_contract.state, "cancel")
        self.assertEqual(pending_contract.state, "cancel")
        new_contract = self.env["hr.contract"].search(
            [
                ("employee_id", "=", self.employee.id),
                (
                    "reference_id",
                    "=",
                    self.env.ref("zhr_ajustes.hr_contract_reference_contract").id,
                ),
            ],
            limit=1,
            order="date_start desc, id desc",
        )
        self.assertEqual(new_contract.name, "Contrato - Empleado Consulta")
        self.assertEqual(new_contract.fecha_contrato, date(2026, 8, 1))
        self.assertEqual(new_contract.date_start, date(2026, 8, 1))
        self.assertFalse(new_contract.date_end)
        self.assertFalse(new_contract.fecha_finiquito)
        self.assertFalse(new_contract.departure_reason_id)
        self.assertEqual(new_contract.state, "open")

    def test_duplicate_contract_wizard_closes_original_and_opens_copy(self):
        contract = self.env["hr.contract"].create(
            {
                "name": "Contrato original",
                "employee_id": self.employee.id,
                "date_start": date(2026, 1, 1),
                "fecha_contrato": date(2026, 1, 1),
                "wage": 1000,
                "state": "open",
            }
        )
        wizard = self.env["hr.contract.duplicate.wizard"].create(
            {
                "contract_id": contract.id,
                "date_start": date(2026, 2, 1),
                "reference_id": self.env.ref(
                    "zhr_ajustes.hr_contract_reference_contract"
                ).id,
            }
        )

        action = wizard.action_confirm()
        new_contract = self.env["hr.contract"].browse(action["res_id"])

        self.assertEqual(contract.state, "expired")
        self.assertEqual(contract.date_end, date(2026, 1, 31))
        self.assertEqual(new_contract.name, "Contrato - Empleado Consulta")
        self.assertEqual(new_contract.fecha_contrato, date(2026, 1, 1))
        self.assertEqual(
            new_contract.reference_id,
            self.env.ref("zhr_ajustes.hr_contract_reference_contract"),
        )
        self.assertEqual(new_contract.date_start, date(2026, 2, 1))
        self.assertFalse(new_contract.date_end)
        self.assertFalse(new_contract.fecha_finiquito)
        self.assertFalse(new_contract.departure_reason_id)
        self.assertEqual(new_contract.state, "draft")
        self.assertEqual(new_contract.employee_id, contract.employee_id)
        self.assertEqual(new_contract.wage, contract.wage)

    def test_duplicate_contract_reference_uses_employee_contract_date_when_origin_is_empty(self):
        self.employee.fecha_contrato = date(2026, 1, 1)
        contract = self.env["hr.contract"].create(
            {
                "name": "Contrato original",
                "employee_id": self.employee.id,
                "date_start": date(2026, 1, 1),
                "wage": 1000,
                "state": "open",
            }
        )
        wizard = self.env["hr.contract.duplicate.wizard"].create(
            {
                "contract_id": contract.id,
                "date_start": date(2026, 2, 1),
                "reference_id": self.env.ref(
                    "zhr_ajustes.hr_contract_reference_contract"
                ).id,
            }
        )

        action = wizard.action_confirm()
        new_contract = self.env["hr.contract"].browse(action["res_id"])

        self.assertEqual(new_contract.fecha_contrato, date(2026, 1, 1))
        self.assertEqual(new_contract.date_start, date(2026, 2, 1))

    def test_duplicate_contract_wizard_uses_annex_reference(self):
        contract = self.env["hr.contract"].create(
            {
                "name": "Contrato original",
                "employee_id": self.employee.id,
                "date_start": date(2026, 1, 1),
                "date_end": date(2026, 3, 31),
                "fecha_contrato": date(2026, 1, 1),
                "fecha_finiquito": date(2026, 3, 31),
                "wage": 1000,
                "state": "open",
            }
        )
        wizard = self.env["hr.contract.duplicate.wizard"].create(
            {
                "contract_id": contract.id,
                "date_start": date(2026, 2, 1),
                "reference_id": self.env.ref(
                    "zhr_ajustes.hr_contract_reference_annex_ipc"
                ).id,
            }
        )

        action = wizard.action_confirm()
        new_contract = self.env["hr.contract"].browse(action["res_id"])

        self.assertEqual(new_contract.name, "Anexo IPC - Empleado Consulta")
        self.assertEqual(contract.state, "expired")
        self.assertEqual(new_contract.fecha_contrato, date(2026, 1, 1))
        self.assertEqual(new_contract.date_start, date(2026, 2, 1))
        self.assertEqual(new_contract.fecha_finiquito, date(2026, 3, 31))
        self.assertEqual(new_contract.date_end, date(2026, 3, 31))
        self.assertEqual(
            new_contract.reference_id,
            self.env.ref("zhr_ajustes.hr_contract_reference_annex_ipc"),
        )
        self.assertEqual(new_contract.state, "open")

    def test_annex_reference_is_excluded_from_contract_gap_validation(self):
        annex_reference = self.env.ref("zhr_ajustes.hr_contract_reference_annex_multiple")
        employee = self.env["hr.employee"].create(
            {
                "name": "Empleado Anexo Sin Continuidad",
                "company_id": self.env.company.id,
            }
        )
        self.env["hr.contract"].create(
            {
                "name": "Contrato base",
                "employee_id": employee.id,
                "date_start": date(2026, 7, 1),
                "date_end": date(2026, 7, 10),
                "wage": 1000,
                "state": "expired",
            }
        )
        renewal_reference = self.env["hr.contract.reference"].create(
            {
                "name": "Anexo Renovacion",
                "reference_type": "contract",
                "sequence": 75,
            }
        )
        self.env["hr.contract"].create(
            {
                "name": "Anexo Renovacion",
                "employee_id": employee.id,
                "reference_id": renewal_reference.id,
                "date_start": date(2026, 7, 11),
                "date_end": date(2026, 7, 22),
                "wage": 1000,
                "state": "expired",
            }
        )

        annex_contract = self.env["hr.contract"].create(
            {
                "name": "Anexo Varios",
                "employee_id": employee.id,
                "reference_id": annex_reference.id,
                "date_start": date(2026, 7, 23),
                "date_end": date(2026, 8, 15),
                "wage": 1000,
                "state": "open",
            }
        )

        self.assertEqual(annex_contract.reference_id.reference_type, "annex")
        self.assertEqual(annex_contract.state, "open")

    def test_renewal_annex_extends_contract_without_overlap_error(self):
        renewal_reference = self.env["hr.contract.reference"].create(
            {
                "name": "Anexo Renovacion",
                "reference_type": "contract",
                "sequence": 75,
            }
        )
        contract = self.env["hr.contract"].create(
            {
                "name": "Contrato original",
                "employee_id": self.employee.id,
                "date_start": date(2026, 1, 1),
                "date_end": date(2026, 7, 10),
                "fecha_contrato": date(2026, 1, 1),
                "fecha_finiquito": date(2026, 7, 10),
                "wage": 1000,
                "state": "open",
            }
        )
        wizard = self.env["hr.contract.duplicate.wizard"].create(
            {
                "contract_id": contract.id,
                "date_start": date(2026, 7, 10),
                "reference_id": renewal_reference.id,
            }
        )

        action = wizard.action_confirm()
        renewal_contract = self.env["hr.contract"].browse(action["res_id"])
        renewal_contract.write(
            {
                "fecha_finiquito": date(2026, 12, 31),
            }
        )

        self.assertEqual(contract.state, "expired")
        self.assertEqual(contract.date_end, date(2026, 7, 10))
        self.assertEqual(renewal_contract.name, "Anexo Renovacion - Empleado Consulta")
        self.assertEqual(renewal_contract.state, "open")
        self.assertEqual(renewal_contract.fecha_contrato, date(2026, 1, 1))
        self.assertEqual(renewal_contract.date_start, date(2026, 7, 10))
        self.assertEqual(renewal_contract.date_end, date(2026, 12, 31))

    def test_indefinite_renewal_annex_sets_indefinite_contract_type(self):
        indefinite_type = self.env["hr.contract.type"].search(
            [("name", "=ilike", "Indefinido")],
            limit=1,
        )
        if not indefinite_type:
            indefinite_type = self.env["hr.contract.type"].create(
                {"name": "Indefinido"}
            )
        fixed_term_type = self.env["hr.contract.type"].create(
            {"name": "Plazo Fijo Test"}
        )
        renewal_reference = self.env["hr.contract.reference"].create(
            {
                "name": "Anexo Renovacion Indefinido",
                "reference_type": "contract",
                "sequence": 76,
            }
        )
        contract = self.env["hr.contract"].create(
            {
                "name": "Contrato plazo fijo",
                "employee_id": self.employee.id,
                "contract_type_id": fixed_term_type.id,
                "date_start": date(2026, 1, 1),
                "date_end": date(2026, 7, 10),
                "fecha_contrato": date(2026, 1, 1),
                "fecha_finiquito": date(2026, 7, 10),
                "wage": 1000,
                "state": "open",
            }
        )
        wizard = self.env["hr.contract.duplicate.wizard"].create(
            {
                "contract_id": contract.id,
                "date_start": date(2026, 7, 10),
                "reference_id": renewal_reference.id,
            }
        )

        action = wizard.action_confirm()
        renewal_contract = self.env["hr.contract"].browse(action["res_id"])

        self.assertEqual(contract.state, "expired")
        self.assertEqual(renewal_contract.name, "Anexo Renovacion Indefinido - Empleado Consulta")
        self.assertEqual(renewal_contract.state, "open")
        self.assertEqual(renewal_contract.contract_type_id, indefinite_type)
        self.assertEqual(renewal_contract.fecha_contrato, date(2026, 1, 1))
        self.assertEqual(renewal_contract.date_start, date(2026, 7, 10))
        self.assertFalse(renewal_contract.date_end)

    def test_duplicate_contract_requires_later_start_date(self):
        contract = self.env["hr.contract"].create(
            {
                "name": "Contrato original",
                "employee_id": self.employee.id,
                "date_start": date(2026, 1, 1),
                "wage": 1000,
            }
        )
        wizard = self.env["hr.contract.duplicate.wizard"].create(
            {
                "contract_id": contract.id,
                "date_start": date(2026, 1, 1),
                "reference_id": self.env.ref(
                    "zhr_ajustes.hr_contract_reference_contract"
                ).id,
            }
        )

        with self.assertRaises(ValidationError):
            wizard.action_confirm()

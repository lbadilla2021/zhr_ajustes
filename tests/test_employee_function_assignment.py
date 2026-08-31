from lxml import etree

from odoo import Command
from odoo.exceptions import AccessError, ValidationError
from odoo.tests.common import TransactionCase


class TestEmployeeFunctionAssignment(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.assignment_group = cls.env.ref(
            "zhr_ajustes.group_zhr_employee_function_assignment"
        )
        cls.readonly_group = cls.env.ref(
            "zhr_ajustes.group_zhr_employee_readonly"
        )
        cls.function_manager_group = cls.env.ref(
            "zhr_ajustes.group_zhr_function_manager"
        )
        cls.assignment_user = cls.env["res.users"].create(
            {
                "name": "Asignador de funciones",
                "login": "asignador.funciones@example.com",
                "groups_id": [Command.set(cls.assignment_group.ids)],
            }
        )
        cls.readonly_user = cls.env["res.users"].create(
            {
                "name": "Consulta sin asignación",
                "login": "consulta.sin.asignacion@example.com",
                "groups_id": [Command.set(cls.readonly_group.ids)],
            }
        )
        cls.function_manager_user = cls.env["res.users"].create(
            {
                "name": "Responsable funciones operativas",
                "login": "responsable.funciones.operativas@example.com",
                "groups_id": [Command.set(cls.function_manager_group.ids)],
            }
        )
        cls.employee = cls.env["hr.employee"].create(
            {
                "name": "Empleado con funciones",
                "company_id": cls.env.company.id,
            }
        )
        cls.active_function = cls.env.ref("zhr_ajustes.it_funcion_lavador_1")
        cls.inactive_function = cls.env.ref("zhr_ajustes.it_funcion_operador_1")
        cls.inactive_function.active = False
        cls.employee.funcion_ids = [Command.set(cls.inactive_function.ids)]

    def test_function_catalog_is_owned_by_hr_module(self):
        functions = self.env["it.funcion"].with_context(active_test=False).search([])
        expected_names = {
            "Lavador 1",
            "Lavador 2",
            "Lavador 3",
            "Operador 1",
            "Operador 2",
            "Operador 3",
            "Supervisor 1",
            "Supervisor 2",
        }
        self.assertTrue(expected_names.issubset(set(functions.mapped("name"))))

    def test_function_maintainer_profile_only_changes_active(self):
        self.active_function.with_user(self.function_manager_user).action_archive()
        self.assertFalse(self.active_function.active)

        self.active_function.with_user(
            self.function_manager_user
        ).action_unarchive()
        self.assertTrue(self.active_function.active)

        with self.assertRaises(AccessError):
            self.active_function.with_user(self.function_manager_user).write(
                {"name": "Cambio no permitido"}
            )

    def test_function_maintainer_is_under_hr_tables(self):
        menu = self.env.ref("zhr_ajustes.menu_it_funcion")
        self.assertEqual(
            menu.parent_id,
            self.env.ref("zhr_ajustes.menu_hr_tables_root"),
        )
        self.assertIn(self.function_manager_group, menu.groups_id)
        action = self.env.ref("zhr_ajustes.action_it_funcion")
        self.assertIn("'active_test': False", action.context)

    def test_function_maintainer_view_only_exposes_active_to_manager(self):
        list_view = self.env.ref("zhr_ajustes.view_it_funcion_list")
        manager_arch = self.env["it.funcion"].with_user(
            self.function_manager_user
        ).get_view(view_id=list_view.id, view_type="list")["arch"]
        readonly_arch = self.env["it.funcion"].with_user(
            self.readonly_user
        ).get_view(view_id=list_view.id, view_type="list")["arch"]
        self.assertTrue(etree.fromstring(manager_arch).xpath("//field[@name='active']"))
        self.assertFalse(etree.fromstring(readonly_arch).xpath("//field[@name='active']"))
        self.assertTrue(
            etree.fromstring(readonly_arch).xpath(
                "//field[@name='active_readonly']"
            )
        )

    def test_assignment_profile_inherits_readonly_without_hr_officer(self):
        self.assertTrue(
            self.assignment_user.has_group(
                "zhr_ajustes.group_zhr_employee_readonly"
            )
        )
        self.assertFalse(self.assignment_user.has_group("hr.group_hr_user"))
        values = self.employee.with_user(self.assignment_user).read(["name"])[0]
        self.assertEqual(values["name"], self.employee.name)

    def test_assignment_profile_only_writes_function_tags(self):
        with self.assertRaises(AccessError):
            self.employee.with_user(self.assignment_user).write(
                {"name": "Intento no permitido"}
            )

        self.employee.with_user(self.assignment_user).write(
            {"funcion_ids": [Command.set(self.active_function.ids)]}
        )
        self.assertEqual(
            set(self.employee.with_context(active_test=False).funcion_ids.ids),
            set((self.active_function | self.inactive_function).ids),
        )

    def test_profile_cannot_assign_a_new_inactive_function(self):
        other_employee = self.env["hr.employee"].create(
            {
                "name": "Empleado sin funciones",
                "company_id": self.env.company.id,
            }
        )
        with self.assertRaises(ValidationError):
            other_employee.with_user(self.assignment_user).write(
                {"funcion_ids": [Command.set(self.inactive_function.ids)]}
            )

    def test_readonly_profile_cannot_write_function_tags(self):
        with self.assertRaises(AccessError):
            self.employee.with_user(self.readonly_user).write(
                {"funcion_ids": [Command.set(self.active_function.ids)]}
            )

    def test_employee_form_uses_editable_tags_and_locks_other_fields(self):
        assignment_arch = self.env["hr.employee"].with_user(
            self.assignment_user
        ).get_view(view_type="form")["arch"]
        readonly_arch = self.env["hr.employee"].with_user(
            self.readonly_user
        ).get_view(view_type="form")["arch"]

        assignment_xml = etree.fromstring(assignment_arch)
        readonly_xml = etree.fromstring(readonly_arch)
        assignment_function_fields = assignment_xml.xpath(
            "//field[@name='funcion_ids']"
        )
        readonly_function_fields = readonly_xml.xpath(
            "//field[@name='funcion_ids']"
        )
        self.assertEqual(len(assignment_function_fields), 1)
        self.assertEqual(
            assignment_function_fields[0].get("widget"),
            "many2many_tags",
        )
        self.assertNotEqual(assignment_function_fields[0].get("readonly"), "1")
        self.assertTrue(readonly_function_fields)
        self.assertEqual(readonly_function_fields[0].get("readonly"), "1")
        self.assertTrue(assignment_xml.xpath("//field[@name='name'][@readonly='1']"))

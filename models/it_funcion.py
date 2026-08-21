from odoo import _, fields, models
from odoo.exceptions import AccessError


FUNCTION_DATA = (
    ("it_funcion_lavador_1", "Lavador 1", 10),
    ("it_funcion_lavador_2", "Lavador 2", 20),
    ("it_funcion_lavador_3", "Lavador 3", 30),
    ("it_funcion_operador_1", "Operador 1", 40),
    ("it_funcion_operador_2", "Operador 2", 50),
    ("it_funcion_operador_3", "Operador 3", 60),
    ("it_funcion_supervisor_1", "Supervisor 1", 70),
    ("it_funcion_supervisor_2", "Supervisor 2", 80),
)


class ITFuncion(models.Model):
    _name = "it.funcion"
    _description = "Función operativa"
    _order = "sequence, name"

    name = fields.Char("Nombre", required=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    active_readonly = fields.Boolean(
        string="Activo",
        related="active",
        readonly=True,
    )
    employee_ids = fields.Many2many(
        "hr.employee",
        "it_funcion_hr_employee_rel",
        "funcion_id",
        "employee_id",
        string="Empleados asignados",
        readonly=True,
    )

    def _check_function_manager(self):
        if not self.env.su and not self.env.user.has_group(
            "zhr_ajustes.group_zhr_function_manager"
        ):
            raise AccessError(
                _(
                    "Para activar o desactivar funciones operativas necesita "
                    "el perfil Gestionar funciones operativas."
                )
            )

    def write(self, vals):
        if not self.env.su:
            self._check_function_manager()
            if set(vals) - {"active"}:
                raise AccessError(
                    _(
                        "Este mantenedor solo permite activar o desactivar "
                        "funciones operativas."
                    )
                )
        return super().write(vals)

    def toggle_active(self):
        self._check_function_manager()
        return super().toggle_active()

    def action_archive(self):
        self._check_function_manager()
        return super().action_archive()

    def action_unarchive(self):
        self._check_function_manager()
        return super().action_unarchive()

    def init(self):
        """Reuse legacy Project records and keep their assignments intact."""
        model_data = self.env["ir.model.data"].sudo()
        functions = self.with_context(active_test=False).sudo()

        for xml_name, name, sequence in FUNCTION_DATA:
            new_xmlid = "zhr_ajustes.%s" % xml_name
            legacy_xmlid = "zproyectos_ajustes.%s" % xml_name
            function = self.env.ref(new_xmlid, raise_if_not_found=False)
            if not function:
                function = self.env.ref(legacy_xmlid, raise_if_not_found=False)
            if not function:
                function = functions.search([("name", "=", name)], limit=1)
            if not function:
                function = functions.create(
                    {
                        "name": name,
                        "sequence": sequence,
                    }
                )

            external_id = model_data.search(
                [
                    ("module", "=", "zhr_ajustes"),
                    ("name", "=", xml_name),
                ],
                limit=1,
            )
            values = {
                "model": self._name,
                "res_id": function.id,
                "noupdate": True,
            }
            if external_id:
                external_id.write(values)
            else:
                model_data.create(
                    {
                        "module": "zhr_ajustes",
                        "name": xml_name,
                        **values,
                    }
                )

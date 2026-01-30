from odoo import fields, models
import base64
import io
import csv

class EmployeeFieldUsageReport(models.TransientModel):
    _name = 'employee.field.usage.report'
    _description = 'Genera un reporte de uso de campos en empleados'

    def action_generate_report(self):

        Employee = self.env['hr.employee']
        employees = Employee.search([])
        fields = Employee._fields

        # Creamos buffer CSV (sin librerías externas)
        buffer = io.StringIO()
        writer = csv.writer(buffer)

        # Header del archivo
        writer.writerow(['Nombre del Campo', 'Etiqueta', 'Tipo', 'Almacenado', 'Registros con Valor'])

        # Recorremos todos los campos del modelo
        for field_name, field in fields.items():
            try:
                if field.store:
                    count = Employee.search_count([(field_name, '!=', False)])
                else:
                    count = 0
            except Exception:
                # Si el campo no es searchable, lo saltamos
                count = 'N/A'

            writer.writerow([
                field_name,
                field.string or "",
                field.type,
                field.store,
                count
            ])

        # Convertir a binario
        data = buffer.getvalue().encode('utf-8')
        buffer.close()

        attachment = self.env['ir.attachment'].create({
            'name': 'reporte_campos_empleado.csv',
            'datas': base64.b64encode(data),
            'type': 'binary',
            'mimetype': 'text/csv'
        })

        return {
            'type': 'ir.actions.act_url',
            'url': f"/web/content/{attachment.id}?download=1",
            'target': 'self',
        }


{
    'name': 'Barca Ajustes Modulo HR',
    'version': '1.0',
    'depends': ['hr', 'hr_contract', 'hr_skills', 'analytic'],
    'data': [
        'security/ir.model.access.csv',
        'views/employee_field_usage_view.xml',
        'views/employee_views.xml',
        'views/hr_employee_list_custom.xml',
    ],
    'installable': True,
    'application': False,
}

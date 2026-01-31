{
    'name': 'Barca Ajustes Modulo HR',
    'version': '1.0',
    'depends': ['hr', 'hr_contract', 'hr_skills', 'analytic'],
    'data': [
        'security/ir.model.access.csv',
        'views/employee_field_usage_view.xml',
        'views/employee_views.xml',
        'views/hr_employee_additional_views.xml',
        'views/hr_employee_list_custom.xml',
        'views/hr_prevision_config_views.xml',
        'views/hr_accreditation_views.xml',
        'views/hr_contract_views.xml',
        'views/resource_calendar_views.xml',
        'views/hr_employee_termination_wizard_views.xml',
    ],
    'installable': True,
    'application': False,
}

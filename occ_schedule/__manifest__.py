{
    'name': "occ_hr_employee",
    'summary': "Module for managing and updating employee shift schedules.",

    'description': """
    This module facilitates the management and updating of employee shift schedules within Odoo. 
    It allows for easy creation, modification, and tracking of work shifts, ensuring efficient
    shift planning and workforce management. Perfect for businesses that require organized shift
    rotations and quick updates to staff schedules.
    """,

    'author': "My Company",
    'website': "https://www.yourcompany.com",    #
    'category': 'Uncategorized',
    'version': '0.1',

    'depends': ['base', 'hr'],

    'data': [
        'security/ir.model.access.csv',
        'views/schedule_management.xml',
        'views/set_schedule.xml',
    ],
    'installable': True,
    'application': False,
}

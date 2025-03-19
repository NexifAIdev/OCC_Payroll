{
    'name': "OCC Break",
    'summary': "Module for managing and updating employee shift schedules.",

    'description': """
    This module facilitates the management and updating of employee shift schedules within Odoo. 
    It allows for easy creation, modification, and tracking of work shifts, ensuring efficient
    shift planning and workforce management. Perfect for businesses that require organized shift
    rotations and quick updates to staff schedules.
    """,

    'author': "Andy M.",
    'website': "",    #  
    'category': 'Uncategorized',
    'version': '0.1',

    'depends': ['base', 'hr', 'hr_attendance','occ_hr_employee','occ_custom_payroll'],

    'data': [
        'security/ir.model.access.csv',
        'views/hr_attendance.xml',
    ],
    'installable': True,
    'application': False,
    'assets': {
        'web.assets_backend': [
            'occ_break/static/src/components/attendance_menu/attendance_menu_view.xml',
            'occ_break/static/src/components/attendance_menu/attendance_menu_action.js',
        ]
    }

}

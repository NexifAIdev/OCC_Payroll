# -*- coding: utf-8 -*-
{
    'name': "Occ Overtime",
    'summary': "Manage employee overtime requests",
    'description': """
        This module allows for the management of employee overtime requests,
        including the ability to define overtime types and approve requests.
    """,
    'author': "My Company",
    'website': "https://www.yourcompany.com",
    'category': 'Human Resources',
    'version': '0.1',
    'depends': ['base', 'hr'],  # Ensure 'hr' is included
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
    ],
    'images': ["fa-icon"],
    'installable': True,
    'application': True,  # Set to True if this module is standalone
}

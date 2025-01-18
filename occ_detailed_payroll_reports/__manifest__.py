# -*- coding: utf-8 -*-
{
    'name': "OCC Detailed Payroll",

    'summary': "Short (1 phrase/line) summary of the module's purpose",

    'description': """
    Long description of module's purpose
    """,

    'author': "My Company",
    'website': "https://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','occ_configurations','occ_custom_payroll', 'pentaho_reports_odoo'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/occ_detailed_payroll_view.xml',
        'views/sss_report.xml',
        'views/pagibig_report.xml',
        'views/philhealth_report.xml',
        'report/report.xml',
    ],
}

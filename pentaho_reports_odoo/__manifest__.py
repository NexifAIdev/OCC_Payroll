# -*- encoding: utf-8 -*-

{
    "name": "Pentaho Reports for Odoo v16",
    "version": "16.0",
    "summary": 'Pentaho Report Integration',
    "description": """
-----------
Pentaho - Odoo Report Integration
-----------

Outstanding
-----------
    This module is tested and functional with SQL Reports in version 17.
    Report Designer compatibility confirmed for version 8.3.

Overview
-----------
This module integrates Pentaho’s reporting engine with Odoo, based on work inspired by other Odoo reporting addons.
Report Designer and Java Component

For report designer setup (version 3.9), refer to: Pentaho Report Designer v8.3. Version 5.0+ includes Odoo data source compatibility.
Report Types

Reports can use either:
-----------
    SQL Data Sources: Offers flexibility in data selections, supports advanced SQL features, and does not respect Odoo record rules.
    Odoo Object Data Sources: Uses data directly from Odoo models.

Report Parameters
-----------
Supports both prompted and hidden parameters, including:

    ids: Context IDs for object-based reports.
    user_id and user_name: User details.
    context_lang and context_tz: Language and timezone settings.

Parameters can default based on Pentaho or custom values using pentaho_defaults. Odoo’s UI elements like selection pull-downs and date pickers align with Pentaho parameters.

Setup
-----------
Add system parameters under Settings / Parameters / System Parameters:

    pentaho.server.url for the server URL.
    Database connection details: pentaho.postgres.host, port, login, and password.

Report Actions
-----------
Define reports under Settings / Technical / Actions / Reports:

    Model-linked reports: Accessible through model-specific actions.
    Menu-linked reports: Accessed from a menu, with options to define report types and parameters.

Reports can override default Odoo actions (e.g., invoice prints) or add new actions. The report file (prpt) is stored in the database and must be reloaded if modified.

Limitations
-----------
Currently, object-based reports require a concurrent session for the running user. This may cause issues if Odoo's password encryption is enabled (default).

For more information, read the README.md on the module directory
""",
    "category": "Reporting/Pentaho",
    "author": "WilldooIT",
    'website': 'https://github.com/WilldooIT/Pentaho-Odoo',
    'images': [],
    "depends": ["base",
                "mail",
                "web",
                ],
    "data": ["report_xml_view.xml",
             'wizard/report_prompt.xml',
             'data/config_data.xml',
             ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'assets': {
        'web.assets_backend': [
            'pentaho_reports_odoo/static/src/js/pentaho/action_service.js',
        ],
    },
}
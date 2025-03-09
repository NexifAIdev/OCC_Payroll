{
    "description": """
OCC Configurations
====================
OCC Configurations
    """,

    "name": "OCC Configurations",
    "version": "17.0.1.0.1",
    "summary": "OCC Core Configurations",
    "category": "OCC/Configurations",
    "author": "odoo-occ",
    "license": "AGPL-3",
    "website": "https://github.com/JC-OCC/OCC_Payroll",
    "images": [
        # "static/description/banner.png"
    ],
    "installable": True,
    "application": True,
    "post_init_hook": "main_post_hook",
    "assets": {
        "web.assets_frontend": [
            "occ_configurations/static/src/xml/login_template.xml",
            "occ_configurations/static/src/js/user_ip_address.js",
        ],
    },
    "external_dependencies": {
        "python": [
            "countryinfo",
            "httpx==0.27.2",
            "icecream==2.1.3",
            "httpagentparser==1.9.5",
            "user-agents==2.2.0",
            "pylightxl==1.61",
        ],
    },
    "depends": [
        "base",
        "web",
        "website",
        "ohrms_core",
        "hr",
    ],
    "data": [
		#‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾
		# Security
		#___________________________________________
        "security/security.xml",
        "security/configs/ir.model.access.csv",
        "security/locations/ir.model.access.csv",
        "security/securities/ir.model.access.csv",
		#-------------------------------------------
		#‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾
		# Cron
		#___________________________________________
		#-------------------------------------------
		#‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾
		# Sequence
		#___________________________________________
		#-------------------------------------------
		#‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾
		# Emails
		#___________________________________________
		#-------------------------------------------
		#‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾
		# Views
		#___________________________________________
        "views/configs/tree.xml",
        "views/locations/tree.xml",
        "views/locations/form.xml",
        "views/securities/tree.xml",
        # "views/securities/form.xml",
        "views/hr/form.xml",
		#-------------------------------------------
		#‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾
		# Action Windows
		#___________________________________________
        "views/configs/windows.xml",
        "views/locations/windows.xml",
        "views/securities/windows.xml",
		#-------------------------------------------
		#‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾
		# Action Servers
		#___________________________________________
		#-------------------------------------------
		#‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾
		# Menus
		#___________________________________________
		"views/menuitems.xml",
        "views/configs/menuitems.xml",
        "views/locations/menuitems.xml",
        "views/securities/menuitems.xml",
		#-------------------------------------------
    ]
}
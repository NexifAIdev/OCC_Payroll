{
    "description": """
OCC Payroll Configurations
====================
OCC Payroll Configurations
    """,

    "name": "OCC Custom Payroll",
    "version": "17.0.1.0.1",
    "summary": "OCC Custom Payroll",
    "category": "OCC/Payroll, OCC/Configurations",
    "author": "odoo-occ",
    "license": "AGPL-3",
    "website": "https://github.com/JC-OCC/OCC_Payroll",
    "images": [
        # "static/description/banner.png"
    ],
    "installable": True,
    "application": True,
    # "post_init_hook": "main_post_hook",
    "assets": {
        "web.assets_backend": [
            
        ]
    },
    "depends": [
        "occ_configurations",
    ],
    "data": [
		#‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾
		# Security
		#___________________________________________
        #  "security/security.xml",
        # "security/configs/ir.model.access.csv",
        # "security/hr/ir.model.access.csv",
        # "security/payslip/ir.model.access.csv",
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
        # "views/payroll/tree.xml",
        # "views/payroll/form.xml",
		#-------------------------------------------
		#‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾
		# Action Windows
		#___________________________________________
        # "views/payroll/windows.xml",
		#-------------------------------------------
		#‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾
		# Action Servers
		#___________________________________________
		#-------------------------------------------
		#‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾
		# Menus
		#___________________________________________
		# "views/menuitems.xml",
        # "views/payroll/menuitems.xml",
		#-------------------------------------------
    ]
}
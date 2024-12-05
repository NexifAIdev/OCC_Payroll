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
        "oh_appraisal",
        "occ_configurations",
        "analytic",
    ],
    "data": [
		#‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾
		# Security
		#___________________________________________
		"security/security.xml",
        "security/config/ir.model.access.csv",
        "security/account/ir.model.access.csv",
        "security/attendance/ir.model.access.csv",
        "security/overtime/ir.model.access.csv",
        "security/hr/ir.model.access.csv",
        "security/payslip/ir.model.access.csv",
        "security/payroll/ir.model.access.csv",
        "security/resource/ir.model.access.csv",
		#-------------------------------------------
		#‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾
		# Cron
		#___________________________________________
		#-------------------------------------------
		#‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾
		# Sequence
		#___________________________________________
		# "views/config/sequence.xml",
        # "views/account/windows.xml",
        # "views/attendance/windows.xml",
        # "views/overtime/windows.xml",
        # "views/hr/windows.xml",
        "views/payslip/sequence.xml",
        "views/payroll/sequence.xml",
        # "views/resource/windows.xml",
		#-------------------------------------------
		#‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾
		# Emails
		#___________________________________________
		#-------------------------------------------
		#‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾
		# Search
		#___________________________________________
		# "views/config/search.xml",
        # "views/account/search.xml",
        # "views/attendance/search.xml",
        # "views/overtime/search.xml",
        # "views/hr/search.xml",
        "views/payslip/search.xml",
        # "views/payroll/search.xml",
        # "views/resource/search.xml",
		#-------------------------------------------
		#‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾
		# Views
		#___________________________________________
        # "views/config/tree.xml",
        # "views/account/tree.xml",
        # "views/attendance/tree.xml",
        # "views/overtime/tree.xml",
        # "views/hr/tree.xml",
        "views/payslip/tree.xml",
        "views/payroll/tree.xml",
        # "views/resource/tree.xml",
        # "views/config/form.xml",
		# "views/account/form.xml",
		# "views/attendance/form.xml",
		# "views/overtime/form.xml",
		# "views/hr/form.xml",
		"views/payslip/form.xml",
		"views/payroll/form.xml",
		# "views/resource/form.xml",
		#-------------------------------------------
		#‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾
		# Action Windows
		#___________________________________________
        # "views/config/windows.xml",
        # "views/account/windows.xml",
        # "views/attendance/windows.xml",
        # "views/overtime/windows.xml",
        # "views/hr/windows.xml",
        "views/payslip/windows.xml",
        "views/payroll/windows.xml",
        # "views/resource/windows.xml",
		#-------------------------------------------
		#‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾
		# Action Servers
		#___________________________________________
		# "views/config/server.xml",
		# "views/account/server.xml",
		# "views/attendance/server.xml",
		# "views/overtime/server.xml",
		# "views/hr/server.xml",
		# "views/payslip/server.xml",
		# "views/payroll/server.xml",
		# "views/resource/server.xml",
		#-------------------------------------------
		#‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾
		# Menus
		#___________________________________________
		"views/menuitems.xml",
        # "views/config/menuitems.xml",
        # "views/account/menuitems.xml",
        # "views/attendance/menuitems.xml",
        # "views/overtime/menuitems.xml",
        # "views/hr/menuitems.xml",
        "views/payslip/menuitems.xml",
        "views/payroll/menuitems.xml",
        # "views/resource/menuitems.xml",
		#-------------------------------------------
		#‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾
		# Data
		#___________________________________________
		"data/data.xml",
		#-------------------------------------------
    ]
}
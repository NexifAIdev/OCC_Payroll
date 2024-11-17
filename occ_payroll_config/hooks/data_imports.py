# -*- coding: utf-8 -*-
# Native Python modules
import os
from typing import List

# Local python modules

# Custom python modules
from icecream import ic

# Odoo modules
from odoo import tools

EXCLUDED_SUFFIXES = (
    ".bak.csv",
    ".backup.csv",
    ".excluded.csv",
    ".noload.csv",
    ".skip.csv",
    ".test.csv",
)


def import_csv_data(cr, directory: str, manual_exclusions: List[str] = None):
    """
    Load the records from the csv upon module installation with optional manual exclusions.
    No connections only. Since order is a must if it has connections
    """

    if manual_exclusions is None:
        manual_exclusions = []

    module_path = os.path.join(os.path.dirname(__file__), "..", directory)
    module_path = os.path.abspath(module_path)

    for filename in os.listdir(module_path):
        ic(filename)
        cond = all(
            [
                filename.endswith(".csv"),
                not filename.lower().endswith(EXCLUDED_SUFFIXES),
                filename not in manual_exclusions,
            ]
        )

        if cond:
            file_path = os.path.join(directory, filename)
            tools.convert_file(
                cr,
                "occ_payroll_config",
                file_path,
                None,
                mode="init",
                noupdate=True,
                kind="init",
            )


def import_csv_data_payslip(cr):
    idref = {}
    
    tools.convert_file(
        cr,
        "occ_payroll_config",
        "data/payslip/rate.type.config.csv",
        idref,
        mode="init",
        noupdate=True,
        kind="init",
    )
    
    tools.convert_file(
        cr,
        "occ_payroll_config",
        "data/payslip/rate.type.list.csv",
        idref,
        mode="init",
        noupdate=True,
        kind="init",
    )
    

def import_csv_data_payroll(cr):
    tools.convert_file(
        cr,
        "occ_payroll_config",
        "data/payroll/paycut.configuration.csv",
        None,
        mode="init",
        noupdate=True,
        kind="init",
    )


def main_post_hook(cr):
    import_csv_data(cr, directory="data/configs")
    import_csv_data_payslip(cr)
    import_csv_data_payroll(cr)
    

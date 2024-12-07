from odoo import models, fields, api, tools, exceptions, _
from datetime import datetime
from xlsxwriter.utility import xl_rowcol_to_cell, xl_range
from collections import defaultdict
from lxml import etree
from odoo.exceptions import UserError
from odoo.tools import float_compare, frozendict
from datetime import datetime, date, timedelta
import pandas as pd
import pytz
import io
import xlsxwriter, base64


class InheritHrEmployee(models.Model):
    _inherit = 'hr.employee'
    
    employee_type_id = fields.Many2one(
    comodel_name='hr.employee.types',
    string='Employee Type',
    )


class OccDetailedPayrollReport(models.TransientModel):
    _name = 'occ.detailed.payroll.report'
    _description = 'Occ Detailed Payroll Report'

    excel_file = fields.Binary("Excel File")
    select_date = fields.Selection(
        string="Pay Schedule:",
        selection=[("first", "Payroll of 1-15"), ("second", "Payroll of 16-30")]
    )
    date_from = fields.Date(string="Date From")
    date_to = fields.Date(string="Date to")
    
    multi_company_id = fields.Many2one(
    comodel_name='res.company',
    string='Company',
    )
    
    employee_type_id = fields.Many2one(
    comodel_name='hr.employee.types',
    string='Employee Type',
    )

    @api.onchange("date_from", "date_to")
    def _check_date_range(self):
        if self.date_from and self.date_to:
            date_from = datetime.strptime(
                str(self.date_from + timedelta(hours=8)) + " 00:00:00",
                "%Y-%m-%d %H:%M:%S",
            )
            date_to = datetime.strptime(
                str(self.date_to + timedelta(hours=8)) + " 23:59:59",
                "%Y-%m-%d %H:%M:%S",
            )

            if date_from > date_to:
                raise UserError(
                    _(
                        "Invalid date range. Date To should be greater than or equal to date from."
                    )
                )

    def get_date_range(self):
        if self.date_to and self.date_from:
            date_from = self.date_from.strftime("%B %-d, %Y")
            date_to = self.date_to.strftime("%B %-d, %Y")
            return f"{date_from} - {date_to}"

    def print_occ_detailed_payroll_report(self):

        output = io.BytesIO()
        row = 0
        col = 0

        workbook = xlsxwriter.Workbook(output)

        # FORMATTING
        headerformat = workbook.add_format(
            {
                "align": "left",
                "valign": "bottom",
                "text_wrap": True,
                "font": "Tahoma",
                "font_size": 10,
                "font_color": "#21130d",
                "bg_color": "#FFFFFF",
            }
        )
        
        headerformatbold = workbook.add_format(
            {
                "bold": True,
                "align": "left",
                "valign": "bottom",
                "text_wrap": True,
                "font": "Tahoma",
                "font_size": 10,
                "font_color": "#21130d",
                "bg_color": "#FFFFFF",
            }
        )

        headerdetailbold = workbook.add_format(
            {
                "bold": True,
                "align": "center",
                "valign": "vcenter",
                "text_wrap": True,
                "font": "Tahoma",
                "font_size": 10,
                "font_color": "#21130d",
                "bg_color": "#92D050",
                'border': 1,
                'border_color': 'black',
            }
        )
        
        headerdetailboldnet = workbook.add_format(
            {
                "bold": True,
                "align": "center",
                "valign": "vcenter",
                "text_wrap": True,
                "font": "Tahoma",
                "font_size": 10,
                "font_color": "#21130d",
                "bg_color": "#FFFF00",
                'border': 1,
                'border_color': 'black',
            }
        )
        
        bodydetailbold = workbook.add_format(
            {
                "align": "center",
                "valign": "vcenter",
                "text_wrap": True,
                "font": "Tahoma",
                "font_size": 10,
                "font_color": "#21130d",
                'border': 1,
                'border_color': 'black',
            }
        )
        
        bodydetailboldnet = workbook.add_format(
            {
                "bold": True,
                "align": "center",
                "valign": "vcenter",
                "text_wrap": True,
                "font": "Tahoma",
                "font_size": 10,
                "font_color": "#21130d",
                "bg_color": "#FFFF00",
                'border': 1,
                'border_color': 'black',
            }
        )
        
        bodydetailboldnetcurrency = workbook.add_format(
            {
                "num_format": "#,##0.00",
                "bold": True,
                "align": "center",
                "valign": "vcenter",
                "text_wrap": True,
                "font": "Tahoma",
                "font_size": 10,
                "font_color": "#21130d",
                "bg_color": "#FFFF00",
                "border": 1,
                "border_color": "black",
            }
        )
        
        bodydetailnormalnetcurrency = workbook.add_format(
            {
                "num_format": "#,##0.00",
                "bold": True,
                "align": "center",
                "valign": "vcenter",
                "text_wrap": True,
                "font": "Tahoma",
                "font_size": 10,
                "border": 1,
                "border_color": "black",
            }
        )
        
        bodydetailnormalleft = workbook.add_format(
            {
                "align": "left",
                "valign": "bottom",
                "text_wrap": True,
                "font": "Tahoma",
                "font_size": 10,
                "font_color": "#21130d",
                'border': 1,
                'border_color': 'black',
            }
        )

        dateformat = workbook.add_format(
            {
                "align": "left",
                "valign": "bottom",
                "font": "Tahoma",
                "text_wrap": True,
                "font_size": 10,
                "num_format": "mmmm d, yyyy",
            }
        )

        # Create Worksheet
        # Set the worksheet name based on emp_type
        emp_type = self.employee_type_id.name
        is_details = workbook.add_worksheet(emp_type)

        # Set the worksheet tab color based on emp_type
        if emp_type == 'Regular':
            is_details.set_tab_color('#FF0000')  # Red for 'regular'
        elif emp_type == 'Probationary':
            is_details.set_tab_color('#8A2BE2')  # Violet for 'probationary'
        elif emp_type == 'Trainee':
            is_details.set_tab_color('#00B050')  # Green for 'probationary'
        elif emp_type == 'Consultant':
            is_details.set_tab_color('#FFFF00')  # Yellow for 'probationary'

        date_range = self.get_date_range()
        current_datetime = datetime.now(pytz.timezone("Asia/Manila")).date()
        
        # Freeze columns A to C from the top (freeze at A1 to C1)
        is_details.freeze_panes(0, 3)
        
        # Set column widths
        is_details.set_column('B:B', 45)  # Set width for column B
        is_details.set_column('C:C', 32)  # Set width for column D
        is_details.set_column('D:D', 25)  # Set width for column D
        is_details.set_column('E:E', 35)  # Set width for column E
        is_details.set_column('F:F', 20)  # Set width for column F

        # Header Main
        is_details.write('B1', "One Contact Center Inc.", headerformatbold)
        is_details.write('B2', f"{emp_type} Payroll", headerformatbold)     
        is_details.write('B3', f"Attendance: {date_range}", headerformat) 
        is_details.write('B4', current_datetime, dateformat)            
        
        if emp_type == "Trainee":
            headers = [
                (" ", headerdetailbold),
                ("NAME", headerdetailbold),
                ("CAMPAIGN", headerdetailbold),
                ("HIRE DATE", headerdetailbold),
                ("BASIC SALARY", headerdetailbold),
                ("ABSENCES/ LATE/ UNDERTIME", headerdetailbold),
                ("OVERTIME", headerdetailbold),
                ("OTHER TAXABLE INCOME", headerdetailbold),
                ("DE MENIMIS", headerdetailbold),
                ("RETENTION BONUS", headerdetailboldnet),
                ("OTHER NON TAXABLE INCOME", headerdetailboldnet),
                ("GROSS INCOME", headerdetailbold),
                ("SSS", headerdetailbold),
                ("SSS WISP", headerdetailbold),
                ("PHIC", headerdetailbold),
                ("HDMF", headerdetailbold),
                ("Additional HDMF", headerdetailbold),
                ("WTAX", headerdetailbold),
                ("TOTAL DEDUCTIONS", headerdetailbold),
                ("NET PAY", headerdetailboldnet),
                ("SSS EC SHARE", headerdetailbold),
                ("SSS ER SHARE", headerdetailbold),
                ("SSS WISPER", headerdetailbold),
                ("PHIC ER SHARE", headerdetailbold),
                ("HDMF ER SHARE", headerdetailbold)
            ]
        elif emp_type == "Consultant":
            headers = [
                (" ", headerdetailbold),
                ("EMPLOYEE ID", headerdetailbold),
                ("NAME", headerdetailbold),
                ("HIRE DATE", headerdetailbold),
                ("BASIC SALARY", headerdetailbold),
                ("Allowance & Reimbursable Allowance ABSENCES / LATE / UNDERTIME", headerdetailbold),
                ("OVERTIME", headerdetailbold),
                ("OTHER TAXABLE INCOME", headerdetailbold),
                ("DE MENIMIS", headerdetailbold),
                ("DAILY ALLOWANCE", headerdetailboldnet),
                ("OTHER NON TAXABLE INCOME", headerdetailboldnet),
                ("GROSS INCOME", headerdetailbold),
                ("SSS", headerdetailbold),
                ("SSS WISP", headerdetailbold),
                ("PHIC", headerdetailbold),
                ("HDMF", headerdetailbold),
                ("Additional HDMF", headerdetailbold),
                ("WTAX", headerdetailbold),
                ("TOTAL DEDUCTIONS", headerdetailbold),
                ("NET PAY", headerdetailboldnet)
            ]
        elif emp_type == "Probitionary":
            headers = [
                (" ", headerdetailbold),
                ("NAME", headerdetailbold),
                ("CAMPAIGN", headerdetailbold),
                ("HIRE DATE", headerdetailbold),
                ("BASIC SALARY", headerdetailbold),
                ("ABSENCES/ LATE/ UNDERTIME", headerdetailbold),
                ("OVERTIME", headerdetailbold),
                ("OTHER TAXABLE INCOME", headerdetailbold),
                ("DE MENIMIS", headerdetailbold),
                ("RETENTION BONUS", headerdetailboldnet),
                ("OTHER NON TAXABLE INCOME", headerdetailboldnet),
                ("GROSS INCOME", headerdetailbold),
                ("SSS", headerdetailbold),
                ("SSS WISP", headerdetailbold),
                ("PHIC", headerdetailbold),
                ("HDMF", headerdetailbold),
                ("Additional HDMF", headerdetailbold),
                ("WTAX", headerdetailbold),
                ("TOTAL DEDUCTIONS", headerdetailbold),
                ("NET PAY", headerdetailboldnet),
                ("SSS EC SHARE", headerdetailbold),
                ("SSS ER SHARE", headerdetailbold),
                ("SSS WISPER", headerdetailbold),
                ("PHIC ER SHARE", headerdetailbold),
                ("HDMF ER SHARE", headerdetailbold)
            ]            
        else:
            headers = [
                (" ", headerdetailbold),
                ("NAME", headerdetailbold),
                ("DEPARTMENT", headerdetailbold),
                ("HIRE DATE", headerdetailbold),
                ("BASIC SALARY", headerdetailbold),
                ("ABSENCES/ LATE/ UNDERTIME", headerdetailbold),
                ("OVERTIME", headerdetailbold),
                ("OTHER TAXABLE INCOME", headerdetailbold),
                ("DE MENIMIS", headerdetailbold),
                ("RETENTION BONUS", headerdetailboldnet),
                ("OTHER NON TAXABLE INCOME", headerdetailboldnet),
                ("GROSS INCOME", headerdetailbold),
                ("SSS", headerdetailbold),
                ("SSS WISP", headerdetailbold),
                ("PHIC", headerdetailbold),
                ("HDMF", headerdetailbold),
                ("Additional HDMF", headerdetailbold),
                ("WTAX", headerdetailbold),
                ("TOTAL DEDUCTIONS", headerdetailbold),
                ("NET PAY", headerdetailboldnet),
                ("SSS EC SHARE", headerdetailbold),
                ("SSS ER SHARE", headerdetailbold),
                ("SSS WISPER", headerdetailbold),
                ("PHIC ER SHARE", headerdetailbold),
                ("HDMF ER SHARE", headerdetailbold)
            ]

        # Write headers starting from B6
        row = 5  # Starting row
        col = 0  # Starting column (B column)

        # Loop through the header list and write each header with the corresponding format
        for header, format in headers:
            is_details.write(row, col, header, format)
            col += 1  # Move to the next column

        # Apply autofilter to the range B6 to Y6 (adjust as necessary)
        is_details.autofilter('A6:Y6')
        
        if emp_type == "Trainee":
            detail_body_query = f"""    
            SELECT  
                ROW_NUMBER() OVER (ORDER BY he.name) AS row_num,               -- 0
                he.name AS emp_name,                                           -- 1
                hd.name->>'en_US' AS department,                               -- 2
                TO_CHAR(he.joining_date, 'MM/DD/YYYY') AS hired_date,          -- 3
                het.name AS emp_type,                                          -- 4
                rc.name AS company,                                            -- 5
                (hc.wage / 2)::NUMERIC AS basic_sal,                           -- 6
                SUM(hp_wages_cte.wages)::NUMERIC AS wages,                     -- 7
                0.00 AS absent_late_undertime,								   -- 8
                0.00 AS overtime,											   -- 9
                0.00 AS other_tax_income,									   -- 10
                0.00 AS de_menimis,											   -- 11
                0.00 AS retention_bonus,									   -- 12
                0.00 AS other_non_tax_income,								   -- 13
                0.00 AS gross_income,										   -- 14
                0.00 AS sss,												   -- 15
                0.00 AS sss_wisp,											   -- 16
                0.00 AS phic,												   -- 17
                200.00 AS hdmf,												   -- 18
                0.00 AS addnl_hdmf,											   -- 19
                0.00 AS wtx,												   -- 20
                0.00 AS total_deduction,									   -- 21
                0.00 AS net_pay,											   -- 22
                30.00 AS sss_ec_share,										   -- 23
                0.00 AS sss_er_share,										   -- 24
                0.00 AS sss_whisper,										   -- 25
                0.00 AS phic_er_share,										   -- 26
                200.00 AS hdmf_er_share										   -- 27

            FROM hr_payslip hp 
            LEFT JOIN hr_employee he ON he.id = hp.employee_id
            LEFT JOIN hr_department hd ON hd.id = he.department_id
            LEFT JOIN res_company rc ON rc.id = he.company_id
            LEFT JOIN hr_employee_types het ON het.id = he.employee_type_id
            LEFT JOIN hr_contract hc ON hc.employee_id = he.id 
                AND hc.department_id = hd.id
            LEFT JOIN (
                SELECT  
                    (hc.wage / 2)::NUMERIC AS wages,
                    hp.id AS payslip_id
                FROM hr_payslip hp
                LEFT JOIN hr_contract hc ON hc.employee_id = hp.employee_id
                WHERE hc.state = 'open'
            ) hp_wages_cte ON hp_wages_cte.payslip_id = hp.id

            WHERE hc.state = 'open'
            AND rc.id = {self.multi_company_id.id}
            AND he.employee_type_id = {self.employee_type_id.id}
            AND hp.date_from::DATE BETWEEN '{self.date_from}' AND '{self.date_to}'

            GROUP BY 
                he.name, hd.name, he.joining_date, het.name, rc.name, hc.wage;
            """
            params = (self.multi_company_id.id, self.employee_type_id.id, self.date_from, self.date_to)
        
            # Execute the query with parameters
            self._cr.execute(detail_body_query, params)
            detail_body_row = self._cr.fetchall()
            
        elif emp_type == "Consultant":
            detail_body_query = f"""
            SELECT  
                ROW_NUMBER() OVER (ORDER BY he.name) AS row_num,               -- 0
                he.name AS emp_name,                                           -- 1
                hd.name->>'en_US' AS department,                               -- 2
                TO_CHAR(he.joining_date, 'MM/DD/YYYY') AS hired_date,          -- 3
                het.name AS emp_type,                                          -- 4
                rc.name AS company,                                            -- 5
                (hc.wage / 2)::NUMERIC AS basic_sal,                           -- 6
                SUM(hp_wages_cte.wages)::NUMERIC AS wages,                     -- 7
                0.00 AS absent_late_undertime,								   -- 8
                0.00 AS overtime,											   -- 9
                0.00 AS other_tax_income,									   -- 10
                0.00 AS de_menimis,											   -- 11
                0.00 AS retention_bonus,									   -- 12
                0.00 AS other_non_tax_income,								   -- 13
                0.00 AS gross_income,										   -- 14
                0.00 AS sss,												   -- 15
                0.00 AS sss_wisp,											   -- 16
                0.00 AS phic,												   -- 17
                200.00 AS hdmf,												   -- 18
                0.00 AS addnl_hdmf,											   -- 19
                0.00 AS wtx,												   -- 20
                0.00 AS total_deduction,									   -- 21
                0.00 AS net_pay,											   -- 22
                30.00 AS sss_ec_share,										   -- 23
                0.00 AS sss_er_share,										   -- 24
                0.00 AS sss_whisper,										   -- 25
                0.00 AS phic_er_share,										   -- 26
                200.00 AS hdmf_er_share										   -- 27

            FROM hr_payslip hp 
            LEFT JOIN hr_employee he ON he.id = hp.employee_id
            LEFT JOIN hr_department hd ON hd.id = he.department_id
            LEFT JOIN res_company rc ON rc.id = he.company_id
            LEFT JOIN hr_employee_types het ON het.id = he.employee_type_id
            LEFT JOIN hr_contract hc ON hc.employee_id = he.id 
                AND hc.department_id = hd.id
            LEFT JOIN (
                SELECT  
                    (hc.wage / 2)::NUMERIC AS wages,
                    hp.id AS payslip_id
                FROM hr_payslip hp
                LEFT JOIN hr_contract hc ON hc.employee_id = hp.employee_id
                WHERE hc.state = 'open'
            ) hp_wages_cte ON hp_wages_cte.payslip_id = hp.id

            WHERE hc.state = 'open'
            AND rc.id = {self.multi_company_id.id}
            AND he.employee_type_id = {self.employee_type_id.id}
            AND hp.date_from::DATE BETWEEN '{self.date_from}' AND '{self.date_to}'

            GROUP BY 
                he.name, hd.name, he.joining_date, het.name, rc.name, hc.wage;
            """
            params = (self.multi_company_id.id, self.employee_type_id.id, self.date_from, self.date_to)
        
            # Execute the query with parameters
            self._cr.execute(detail_body_query, params)
            detail_body_row = self._cr.fetchall()
            
        elif emp_type == "Probitionary":
            detail_body_query = f"""
            SELECT  
                ROW_NUMBER() OVER (ORDER BY he.name) AS row_num,               -- 0
                he.name AS emp_name,                                           -- 1
                hd.name->>'en_US' AS department,                               -- 2
                TO_CHAR(he.joining_date, 'MM/DD/YYYY') AS hired_date,          -- 3
                het.name AS emp_type,                                          -- 4
                rc.name AS company,                                            -- 5
                (hc.wage / 2)::NUMERIC AS basic_sal,                           -- 6
                SUM(hp_wages_cte.wages)::NUMERIC AS wages,                     -- 7
                0.00 AS absent_late_undertime,								   -- 8
                0.00 AS overtime,											   -- 9
                0.00 AS other_tax_income,									   -- 10
                0.00 AS de_menimis,											   -- 11
                0.00 AS retention_bonus,									   -- 12
                0.00 AS other_non_tax_income,								   -- 13
                0.00 AS gross_income,										   -- 14
                0.00 AS sss,												   -- 15
                0.00 AS sss_wisp,											   -- 16
                0.00 AS phic,												   -- 17
                200.00 AS hdmf,												   -- 18
                0.00 AS addnl_hdmf,											   -- 19
                0.00 AS wtx,												   -- 20
                0.00 AS total_deduction,									   -- 21
                0.00 AS net_pay,											   -- 22
                30.00 AS sss_ec_share,										   -- 23
                0.00 AS sss_er_share,										   -- 24
                0.00 AS sss_whisper,										   -- 25
                0.00 AS phic_er_share,										   -- 26
                200.00 AS hdmf_er_share										   -- 27

            FROM hr_payslip hp 
            LEFT JOIN hr_employee he ON he.id = hp.employee_id
            LEFT JOIN hr_department hd ON hd.id = he.department_id
            LEFT JOIN res_company rc ON rc.id = he.company_id
            LEFT JOIN hr_employee_types het ON het.id = he.employee_type_id
            LEFT JOIN hr_contract hc ON hc.employee_id = he.id 
                AND hc.department_id = hd.id
            LEFT JOIN (
                SELECT  
                    (hc.wage / 2)::NUMERIC AS wages,
                    hp.id AS payslip_id
                FROM hr_payslip hp
                LEFT JOIN hr_contract hc ON hc.employee_id = hp.employee_id
                WHERE hc.state = 'open'
            ) hp_wages_cte ON hp_wages_cte.payslip_id = hp.id

            WHERE hc.state = 'open'
            AND rc.id = {self.multi_company_id.id}
            AND he.employee_type_id = {self.employee_type_id.id}
            AND hp.date_from::DATE BETWEEN '{self.date_from}' AND '{self.date_to}'

            GROUP BY 
                he.name, hd.name, he.joining_date, het.name, rc.name, hc.wage;
            """
            params = (self.multi_company_id.id, self.employee_type_id.id, self.date_from, self.date_to)
        
            # Execute the query with parameters
            self._cr.execute(detail_body_query, params)
            detail_body_row = self._cr.fetchall()
                                    
        else:
            detail_body_query = f"""
            SELECT  
                ROW_NUMBER() OVER (ORDER BY he.name) AS row_num,               -- 0
                he.name AS emp_name,                                           -- 1
                hd.name->>'en_US' AS department,                               -- 2
                TO_CHAR(he.joining_date, 'MM/DD/YYYY') AS hired_date,          -- 3
                het.name AS emp_type,                                          -- 4
                rc.name AS company,                                            -- 5
                (hc.wage / 2)::NUMERIC AS basic_sal,                           -- 6
                SUM(hp_wages_cte.wages)::NUMERIC AS wages,                     -- 7
                0.00 AS absent_late_undertime,								   -- 8
                0.00 AS overtime,											   -- 9
                0.00 AS other_tax_income,									   -- 10
                0.00 AS de_menimis,											   -- 11
                0.00 AS retention_bonus,									   -- 12
                0.00 AS other_non_tax_income,								   -- 13
                0.00 AS gross_income,										   -- 14
                0.00 AS sss,												   -- 15
                0.00 AS sss_wisp,											   -- 16
                0.00 AS phic,												   -- 17
                200.00 AS hdmf,												   -- 18
                0.00 AS addnl_hdmf,											   -- 19
                0.00 AS wtx,												   -- 20
                0.00 AS total_deduction,									   -- 21
                0.00 AS net_pay,											   -- 22
                30.00 AS sss_ec_share,										   -- 23
                0.00 AS sss_er_share,										   -- 24
                0.00 AS sss_whisper,										   -- 25
                0.00 AS phic_er_share,										   -- 26
                200.00 AS hdmf_er_share										   -- 27

            FROM hr_payslip hp 
            LEFT JOIN hr_employee he ON he.id = hp.employee_id
            LEFT JOIN hr_department hd ON hd.id = he.department_id
            LEFT JOIN res_company rc ON rc.id = he.company_id
            LEFT JOIN hr_employee_types het ON het.id = he.employee_type_id
            LEFT JOIN hr_contract hc ON hc.employee_id = he.id 
                AND hc.department_id = hd.id
            LEFT JOIN (
                SELECT  
                    (hc.wage / 2)::NUMERIC AS wages,
                    hp.id AS payslip_id
                FROM hr_payslip hp
                LEFT JOIN hr_contract hc ON hc.employee_id = hp.employee_id
                WHERE hc.state = 'open'
            ) hp_wages_cte ON hp_wages_cte.payslip_id = hp.id

            WHERE hc.state = 'open'
            AND rc.id = {self.multi_company_id.id}
            AND he.employee_type_id = {self.employee_type_id.id}
            AND hp.date_from::DATE BETWEEN '{self.date_from}' AND '{self.date_to}'

            GROUP BY 
                he.name, hd.name, he.joining_date, het.name, rc.name, hc.wage;
            """
            params = (self.multi_company_id.id, self.employee_type_id.id, self.date_from, self.date_to)
            
            # Execute the query with parameters
            self._cr.execute(detail_body_query, params)
            detail_body_row = self._cr.fetchall()
        
        # Write the detail rows starting from row 6 (the next row after headers)
        row = 6  # Start from row 6, just below the headers
        
        if emp_type == "Trainee":
            for detail_body in detail_body_row:
                col = 0  # Reset column to 0 for each row
                is_details.set_row(row, 15)

                # Write the details to the columns (adjust based on the columns in detail_body)
                is_details.write(row, col, detail_body[0], bodydetailbold)  # Employee Count
                col += 1
                is_details.write(row, col, detail_body[1].upper(), bodydetailnormalleft)  # Employee Name
                col += 1
                is_details.write(row, col, detail_body[2].upper(), bodydetailnormalleft)  # Department
                col += 1
                is_details.write(row, col, detail_body[3], bodydetailbold)  # Hire Date
                col += 1
                # Round the Basic Salary to 2 decimal places before writing it to the cell
                basic_salary = round(detail_body[6], 2)
                is_details.write(row, col, basic_salary, bodydetailboldnetcurrency)  # Basic Salary
                col += 1
                
                is_details.write(row, col, detail_body[8], bodydetailnormalnetcurrency)  # Absent Late Undertime
                col += 1
                is_details.write(row, col, detail_body[9], bodydetailnormalnetcurrency)  # Overtime
                col += 1
                is_details.write(row, col, detail_body[10], bodydetailnormalnetcurrency)  # Other Tax Income
                col += 1
                is_details.write(row, col, detail_body[11], bodydetailnormalnetcurrency)  # De Minimis
                col += 1
                is_details.write(row, col, detail_body[12], bodydetailnormalnetcurrency)  # Retention Bonus
                col += 1
                is_details.write(row, col, detail_body[13], bodydetailboldnetcurrency)  # Other Non-Tax Income
                col += 1
                is_details.write(row, col, detail_body[14], bodydetailnormalnetcurrency)  # Gross Income
                col += 1
                is_details.write(row, col, detail_body[15], bodydetailnormalnetcurrency)  # SSS
                col += 1
                is_details.write(row, col, detail_body[16], bodydetailnormalnetcurrency)  # SSS WISP
                col += 1
                is_details.write(row, col, detail_body[17], bodydetailnormalnetcurrency)  # PHIC
                col += 1
                is_details.write(row, col, detail_body[18], bodydetailnormalnetcurrency)  # HDMF
                col += 1
                is_details.write(row, col, detail_body[19], bodydetailnormalnetcurrency)  # Additional HDMF
                col += 1
                is_details.write(row, col, detail_body[20], bodydetailnormalnetcurrency)  # WTX
                col += 1
                is_details.write(row, col, detail_body[21], bodydetailnormalnetcurrency)  # Total Deduction
                col += 1
                is_details.write(row, col, detail_body[22], bodydetailboldnetcurrency)  # Net Pay
                col += 1
                is_details.write(row, col, detail_body[23], bodydetailnormalnetcurrency)  # SSS EC Share
                col += 1
                is_details.write(row, col, detail_body[24], bodydetailnormalnetcurrency)  # SSS ER Share
                col += 1
                is_details.write(row, col, detail_body[25], bodydetailnormalnetcurrency)  # SSS Whisper
                col += 1
                is_details.write(row, col, detail_body[26], bodydetailnormalnetcurrency)  # PHIC ER Share
                col += 1
                is_details.write(row, col, detail_body[27], bodydetailnormalnetcurrency)  # HDMF ER Share
                col += 1
                
                # Increment row for the next employee
                row += 1
                
            # After the loop, write "TOTAL" in the cell below the last hire date row
            is_details.write_blank(row, 0, None, bodydetailbold)  # Column A
            is_details.write_blank(row, 1, None, bodydetailbold)  # Column B
            is_details.write_blank(row, 2, None, bodydetailbold)  # Column C
            is_details.write(row, 3, "TOTAL", bodydetailbold)  # Column D (index 3)
            total_wages = sum(row[7] for row in detail_body_row)  # Sum of wages
            is_details.write(row, 4, round(total_wages, 2), bodydetailboldnetcurrency)
            
        elif emp_type == "Consultant":
            for detail_body in detail_body_row:
                col = 0  # Reset column to 0 for each row
                is_details.set_row(row, 15)

                # Write the details to the columns (adjust based on the columns in detail_body)
                is_details.write(row, col, detail_body[0], bodydetailbold)  # Employee Count
                col += 1
                is_details.write(row, col, detail_body[1].upper(), bodydetailnormalleft)  # Employee Name
                col += 1
                is_details.write(row, col, detail_body[2].upper(), bodydetailnormalleft)  # Department
                col += 1
                is_details.write(row, col, detail_body[3], bodydetailbold)  # Hire Date
                col += 1
                # Round the Basic Salary to 2 decimal places before writing it to the cell
                basic_salary = round(detail_body[6], 2)
                is_details.write(row, col, basic_salary, bodydetailboldnetcurrency)  # Basic Salary
                col += 1
                
                is_details.write(row, col, detail_body[8], bodydetailnormalnetcurrency)  # Absent Late Undertime
                col += 1
                is_details.write(row, col, detail_body[9], bodydetailnormalnetcurrency)  # Overtime
                col += 1
                is_details.write(row, col, detail_body[10], bodydetailnormalnetcurrency)  # Other Tax Income
                col += 1
                is_details.write(row, col, detail_body[11], bodydetailnormalnetcurrency)  # De Minimis
                col += 1
                is_details.write(row, col, detail_body[12], bodydetailnormalnetcurrency)  # Retention Bonus
                col += 1
                is_details.write(row, col, detail_body[13], bodydetailboldnetcurrency)  # Other Non-Tax Income
                col += 1
                is_details.write(row, col, detail_body[14], bodydetailnormalnetcurrency)  # Gross Income
                col += 1
                is_details.write(row, col, detail_body[15], bodydetailnormalnetcurrency)  # SSS
                col += 1
                is_details.write(row, col, detail_body[16], bodydetailnormalnetcurrency)  # SSS WISP
                col += 1
                is_details.write(row, col, detail_body[17], bodydetailnormalnetcurrency)  # PHIC
                col += 1
                is_details.write(row, col, detail_body[18], bodydetailnormalnetcurrency)  # HDMF
                col += 1
                is_details.write(row, col, detail_body[19], bodydetailnormalnetcurrency)  # Additional HDMF
                col += 1
                is_details.write(row, col, detail_body[20], bodydetailnormalnetcurrency)  # WTX
                col += 1
                is_details.write(row, col, detail_body[21], bodydetailnormalnetcurrency)  # Total Deduction
                col += 1
                is_details.write(row, col, detail_body[22], bodydetailboldnetcurrency)  # Net Pay
                col += 1
                is_details.write(row, col, detail_body[23], bodydetailnormalnetcurrency)  # SSS EC Share
                col += 1
                is_details.write(row, col, detail_body[24], bodydetailnormalnetcurrency)  # SSS ER Share
                col += 1
                is_details.write(row, col, detail_body[25], bodydetailnormalnetcurrency)  # SSS Whisper
                col += 1
                is_details.write(row, col, detail_body[26], bodydetailnormalnetcurrency)  # PHIC ER Share
                col += 1
                is_details.write(row, col, detail_body[27], bodydetailnormalnetcurrency)  # HDMF ER Share
                col += 1
                
                # Increment row for the next employee
                row += 1
                
            # After the loop, write "TOTAL" in the cell below the last hire date row
            is_details.write_blank(row, 0, None, bodydetailbold)  # Column A
            is_details.write_blank(row, 1, None, bodydetailbold)  # Column B
            is_details.write_blank(row, 2, None, bodydetailbold)  # Column C
            is_details.write(row, 3, "TOTAL", bodydetailbold)  # Column D (index 3)
            total_wages = sum(row[7] for row in detail_body_row)  # Sum of wages
            is_details.write(row, 4, round(total_wages, 2), bodydetailboldnetcurrency)
            
        elif emp_type == "Probitionary":
            for detail_body in detail_body_row:
                col = 0  # Reset column to 0 for each row
                is_details.set_row(row, 15)

                # Write the details to the columns (adjust based on the columns in detail_body)
                is_details.write(row, col, detail_body[0], bodydetailbold)  # Employee Count
                col += 1
                is_details.write(row, col, detail_body[1].upper(), bodydetailnormalleft)  # Employee Name
                col += 1
                is_details.write(row, col, detail_body[2].upper(), bodydetailnormalleft)  # Department
                col += 1
                is_details.write(row, col, detail_body[3], bodydetailbold)  # Hire Date
                col += 1
                # Round the Basic Salary to 2 decimal places before writing it to the cell
                basic_salary = round(detail_body[6], 2)
                is_details.write(row, col, basic_salary, bodydetailboldnetcurrency)  # Basic Salary
                col += 1

                is_details.write(row, col, detail_body[8], bodydetailnormalnetcurrency)  # Absent Late Undertime
                col += 1
                is_details.write(row, col, detail_body[9], bodydetailnormalnetcurrency)  # Overtime
                col += 1
                is_details.write(row, col, detail_body[10], bodydetailnormalnetcurrency)  # Other Tax Income
                col += 1
                is_details.write(row, col, detail_body[11], bodydetailnormalnetcurrency)  # De Minimis
                col += 1
                is_details.write(row, col, detail_body[12], bodydetailnormalnetcurrency)  # Retention Bonus
                col += 1
                is_details.write(row, col, detail_body[13], bodydetailboldnetcurrency)  # Other Non-Tax Income
                col += 1
                is_details.write(row, col, detail_body[14], bodydetailnormalnetcurrency)  # Gross Income
                col += 1
                is_details.write(row, col, detail_body[15], bodydetailnormalnetcurrency)  # SSS
                col += 1
                is_details.write(row, col, detail_body[16], bodydetailnormalnetcurrency)  # SSS WISP
                col += 1
                is_details.write(row, col, detail_body[17], bodydetailnormalnetcurrency)  # PHIC
                col += 1
                is_details.write(row, col, detail_body[18], bodydetailnormalnetcurrency)  # HDMF
                col += 1
                is_details.write(row, col, detail_body[19], bodydetailnormalnetcurrency)  # Additional HDMF
                col += 1
                is_details.write(row, col, detail_body[20], bodydetailnormalnetcurrency)  # WTX
                col += 1
                is_details.write(row, col, detail_body[21], bodydetailnormalnetcurrency)  # Total Deduction
                col += 1
                is_details.write(row, col, detail_body[22], bodydetailboldnetcurrency)  # Net Pay
                col += 1
                is_details.write(row, col, detail_body[23], bodydetailnormalnetcurrency)  # SSS EC Share
                col += 1
                is_details.write(row, col, detail_body[24], bodydetailnormalnetcurrency)  # SSS ER Share
                col += 1
                is_details.write(row, col, detail_body[25], bodydetailnormalnetcurrency)  # SSS Whisper
                col += 1
                is_details.write(row, col, detail_body[26], bodydetailnormalnetcurrency)  # PHIC ER Share
                col += 1
                is_details.write(row, col, detail_body[27], bodydetailnormalnetcurrency)  # HDMF ER Share
                col += 1
                
                # Increment row for the next employee
                row += 1
                
            # After the loop, write "TOTAL" in the cell below the last hire date row
            is_details.write_blank(row, 0, None, bodydetailbold)  # Column A
            is_details.write_blank(row, 1, None, bodydetailbold)  # Column B
            is_details.write_blank(row, 2, None, bodydetailbold)  # Column C
            is_details.write(row, 3, "TOTAL", bodydetailbold)  # Column D (index 3)
            total_wages = sum(row[7] for row in detail_body_row)  # Sum of wages
            is_details.write(row, 4, round(total_wages, 2), bodydetailboldnetcurrency)
            
        else:    
            for detail_body in detail_body_row:
                col = 0  # Reset column to 0 for each row
                is_details.set_row(row, 15)

                # Write the details to the columns (adjust based on the columns in detail_body)
                is_details.write(row, col, detail_body[0], bodydetailbold)  # Employee Count
                col += 1
                is_details.write(row, col, detail_body[1].upper(), bodydetailnormalleft)  # Employee Name
                col += 1
                is_details.write(row, col, detail_body[2].upper(), bodydetailnormalleft)  # Department
                col += 1
                is_details.write(row, col, detail_body[3], bodydetailbold)  # Hire Date
                col += 1
                # Round the Basic Salary to 2 decimal places before writing it to the cell
                basic_salary = round(detail_body[6], 2)
                is_details.write(row, col, basic_salary, bodydetailboldnetcurrency)  # Basic Salary
                col += 1
                
                is_details.write(row, col, detail_body[8], bodydetailnormalnetcurrency)  # Absent Late Undertime
                col += 1
                is_details.write(row, col, detail_body[9], bodydetailnormalnetcurrency)  # Overtime
                col += 1
                is_details.write(row, col, detail_body[10], bodydetailnormalnetcurrency)  # Other Tax Income
                col += 1
                is_details.write(row, col, detail_body[11], bodydetailnormalnetcurrency)  # De Minimis
                col += 1
                is_details.write(row, col, detail_body[12], bodydetailnormalnetcurrency)  # Retention Bonus
                col += 1
                is_details.write(row, col, detail_body[13], bodydetailboldnetcurrency)  # Other Non-Tax Income
                col += 1
                is_details.write(row, col, detail_body[14], bodydetailnormalnetcurrency)  # Gross Income
                col += 1
                is_details.write(row, col, detail_body[15], bodydetailnormalnetcurrency)  # SSS
                col += 1
                is_details.write(row, col, detail_body[16], bodydetailnormalnetcurrency)  # SSS WISP
                col += 1
                is_details.write(row, col, detail_body[17], bodydetailnormalnetcurrency)  # PHIC
                col += 1
                is_details.write(row, col, detail_body[18], bodydetailnormalnetcurrency)  # HDMF
                col += 1
                is_details.write(row, col, detail_body[19], bodydetailnormalnetcurrency)  # Additional HDMF
                col += 1
                is_details.write(row, col, detail_body[20], bodydetailnormalnetcurrency)  # WTX
                col += 1
                is_details.write(row, col, detail_body[21], bodydetailnormalnetcurrency)  # Total Deduction
                col += 1
                is_details.write(row, col, detail_body[22], bodydetailboldnetcurrency)  # Net Pay
                col += 1
                is_details.write(row, col, detail_body[23], bodydetailnormalnetcurrency)  # SSS EC Share
                col += 1
                is_details.write(row, col, detail_body[24], bodydetailnormalnetcurrency)  # SSS ER Share
                col += 1
                is_details.write(row, col, detail_body[25], bodydetailnormalnetcurrency)  # SSS Whisper
                col += 1
                is_details.write(row, col, detail_body[26], bodydetailnormalnetcurrency)  # PHIC ER Share
                col += 1
                is_details.write(row, col, detail_body[27], bodydetailnormalnetcurrency)  # HDMF ER Share
                col += 1
                
                # Increment row for the next employee
                row += 1
                
            # After the loop, write "TOTAL" in the cell below the last hire date row
            is_details.write_blank(row, 0, None, bodydetailbold)  # Column A
            is_details.write_blank(row, 1, None, bodydetailbold)  # Column B
            is_details.write_blank(row, 2, None, bodydetailbold)  # Column C
            is_details.write(row, 3, "TOTAL", bodydetailbold)  # Column D (index 3)
            total_wages = sum(row[7] for row in detail_body_row)  # Sum of wages
            is_details.write(row, 4, round(total_wages, 2), bodydetailboldnetcurrency)                                    
            
        # Set row height (optional)
        is_details.set_row(row, 15)
                    
        # Close Report
        workbook.close()
        output.seek(0)
        xy = output.read()
        
        file = base64.encodebytes(xy)  
        self.write({"excel_file": file})
        filename = 'occ_detailed_payroll_report.xlsx'

        return {
            "type": "ir.actions.act_url",
            "url": f"/web/content/occ.detailed.payroll.report/{self.id}/excel_file/{filename}?download=true",
            "target": "self",
        }


class InheritHrPayslip(models.Model):
    _inherit = 'hr.payslip'

    def action_print_detailed_payroll(self):
        context = dict(self._context or {})
        active_ids = (
            str(context.get("active_ids", []) or []).replace("[", "(").replace("]", ")")
        )
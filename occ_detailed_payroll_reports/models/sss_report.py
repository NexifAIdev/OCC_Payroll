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


class SSSReport(models.TransientModel):
    _name = 'sss.report'
    _inherit = ['paycut.mixin']
    _description = 'SSS Summary Report'

    excel_file = fields.Binary("Excel File")
    select_date = fields.Selection(
        string="Pay Schedule:",
        selection=[("first", "Payroll of 1-15"), ("second", "Payroll of 16-30")]
    )
    
    paysched_compute = fields.Datetime(
        compute="_compute_paysched",
    )
    
    dates_compute = fields.Datetime(
        compute="_compute_dates",
    )
    
    year = fields.Integer(
        string="Year",
    )
    
    month = fields.Selection(
        selection=lambda self: [(i, f"{i:02}") for i in range(1,13,1)],
        string="Month",
    )
    
    paycut_period_domain = fields.Many2many(
        comodel_name="paycut.configuration",
        string="Pay Schedule Domain"
    )
    
    paycut_period = fields.Many2one(
        comodel_name="paycut.configuration",
        string="Pay Schedule",
        domain="[('id', '=', paycut_period_domain)]",
    )
    
    date_from = fields.Date(string="Date From", readonly=True)
    date_to = fields.Date(string="Date to", readonly=True)
    
    multi_company_id = fields.Many2one(
    comodel_name='res.company',
    string='Company',
    )
    
    employee_type_id = fields.Many2one(
    comodel_name='hr.employee.types',
    string='Employee Type',
    )
    
    @api.depends("year", "month")
    def _compute_paysched(self):
        for rec in self:
            year = rec.year
            month = rec.month
            
            paycut = False
            if year and month:
                pay_sched_ids = rec._get_paycut_period(year, int(month))
                
                paycut = self.env["paycut.configuration"].search(
                    domain=[
                        ("id", "in", [v for k,v in pay_sched_ids.items() if v])
                    ]
                )
                print(paycut)
            
            rec.paycut_period_domain = [(6, 0, paycut.ids)] if paycut else [(5, 0, 0)]
            print(rec.paycut_period_domain)
            
            rec.paysched_compute = fields.Datetime.now()
            
            
    @api.depends("paycut_period")
    def _compute_dates(self):
        for rec in self:
            date_from = rec.date_from
            date_to = rec.date_to
            pay_sched = rec.paycut_period
            year = rec.year
            month = rec.month
            
            print(pay_sched)
            
            if pay_sched and year and month:
                first = pay_sched.start_day
                last = pay_sched.end_day
                
                print(first)
                print(last)
                
                date_from = datetime.strptime(
                    f"{year}-{month}-{first}",
                    "%Y-%m-%d",
                ).date()
                
                date_to = datetime.strptime(
                    f"{year}-{month}-{last}",
                    "%Y-%m-%d",
                ).date()
                
                print(date_from)
                print(date_to)
                
            rec.date_from = date_from
            rec.date_to = date_to
            
            rec.dates_compute = fields.Datetime.now()
            

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

    def print_sss_report(self):

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
        is_details.write('B2', f"{emp_type} SSS Summary Report", headerformatbold)     
        is_details.write('B3', f"Attendance: {date_range}", headerformat) 
        is_details.write('B4', current_datetime, dateformat)            
        
        if emp_type == "Trainee":
            headers = [
                (" ", headerdetailbold),
                ("NAME", headerdetailbold),
                ("CAMPAIGN", headerdetailbold),
                ("SSS NO.", headerdetailbold),
                ("HIRE DATE", headerdetailbold),
                ("SSS", headerdetailbold),
                ("SSS WISP", headerdetailbold),
                ("SSS EC SHARE", headerdetailbold),
                ("SSS ER SHARE", headerdetailbold),
                ("SSS WISPER", headerdetailbold)
            ]
        elif emp_type == "Consultant":
            headers = [
                (" ", headerdetailbold),
                ("EMPLOYEE ID", headerdetailbold),
                ("NAME", headerdetailbold),
                ("SSS NO.", headerdetailbold),
                ("HIRE DATE", headerdetailbold),
                ("SSS", headerdetailbold),
                ("SSS WISP", headerdetailbold)
            ]
        elif emp_type == "Probitionary":
            headers = [
                (" ", headerdetailbold),
                ("NAME", headerdetailbold),
                ("CAMPAIGN", headerdetailbold),
                ("SSS NO.", headerdetailbold),
                ("HIRE DATE", headerdetailbold),
                ("SSS", headerdetailbold),
                ("SSS WISP", headerdetailbold),
                ("SSS EC SHARE", headerdetailbold),
                ("SSS ER SHARE", headerdetailbold),
                ("SSS WISPER", headerdetailbold)
            ]            
        else:
            headers = [
                (" ", headerdetailbold),
                ("NAME", headerdetailbold),
                ("DEPARTMENT", headerdetailbold),
                ("SSS NO.", headerdetailbold),
                ("HIRE DATE", headerdetailbold),
                ("SSS", headerdetailbold),
                ("SSS WISP", headerdetailbold),
                ("SSS EC SHARE", headerdetailbold),
                ("SSS ER SHARE", headerdetailbold),
                ("SSS WISPER", headerdetailbold)
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
                0.00 AS sss,												   -- 6
                0.00 AS sss_wisp,											   -- 7
                30.00 AS sss_ec_share,										   -- 8
                0.00 AS sss_er_share,										   -- 8
                0.00 AS sss_whisper, 										   -- 10
                he.sss_no AS sss_no      									   -- 11

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
                250.00 AS sss,												   -- 6
                0.00 AS sss_wisp,											   -- 7
                30.00 AS sss_ec_share,										   -- 8
                0.00 AS sss_er_share,										   -- 9
                0.00 AS sss_whisper, 										   -- 10
                he.sss_no AS sss_no,      									   -- 11
                he.employee_id AS emp_id                                       -- 12

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
                0.00 AS sss,												   -- 6
                0.00 AS sss_wisp,											   -- 7
                30.00 AS sss_ec_share,										   -- 8
                0.00 AS sss_er_share,										   -- 8
                0.00 AS sss_whisper, 										   -- 10
                he.sss_no AS sss_no      									   -- 11

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
                0.00 AS sss,												   -- 6
                0.00 AS sss_wisp,											   -- 7
                30.00 AS sss_ec_share,										   -- 8
                0.00 AS sss_er_share,										   -- 8
                0.00 AS sss_whisper, 										   -- 10
                he.sss_no AS sss_no      									   -- 11

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
                is_details.write(row, col, detail_body[11].upper(), bodydetailnormalleft)  # SSS No
                col += 1
                is_details.write(row, col, detail_body[3], bodydetailbold)  # Hire Date
                col += 1
                is_details.write(row, col, detail_body[6], bodydetailnormalnetcurrency)  # SSS
                col += 1
                is_details.write(row, col, detail_body[7], bodydetailnormalnetcurrency)  # SSS WISP
                col += 1
                is_details.write(row, col, detail_body[8], bodydetailnormalnetcurrency)  # SSS EC Share
                col += 1
                is_details.write(row, col, detail_body[9], bodydetailnormalnetcurrency)  # SSS ER Share
                col += 1
                is_details.write(row, col, detail_body[10], bodydetailnormalnetcurrency)  # SSS Whisper
                col += 1
                
                # Increment row for the next employee
                row += 1
                
            # After the loop, write "TOTAL" in the cell below the last hire date row
            is_details.write_blank(row, 0, None, bodydetailbold)  # Column A
            is_details.write_blank(row, 1, None, bodydetailbold)  # Column B
            is_details.write_blank(row, 2, None, bodydetailbold)  # Column C
            is_details.write_blank(row, 3, None, bodydetailbold)  # Column C
            is_details.write(row, 4, "TOTAL", bodydetailbold)  # Column D (index 3)
            total_wages = sum(row[6] for row in detail_body_row)  # Sum of wages
            is_details.write(row, 5, round(total_wages, 2), bodydetailboldnetcurrency)
            
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
                is_details.write(row, col, detail_body[11].upper(), bodydetailnormalleft)  # SSS No
                col += 1
                is_details.write(row, col, detail_body[3], bodydetailbold)  # Hire Date
                col += 1
                is_details.write(row, col, detail_body[6], bodydetailnormalnetcurrency)  # SSS
                col += 1
                is_details.write(row, col, detail_body[7], bodydetailnormalnetcurrency)  # SSS WISP
                col += 1
                
                # Increment row for the next employee
                row += 1
                
            # After the loop, write "TOTAL" in the cell below the last hire date row
            is_details.write_blank(row, 0, None, bodydetailbold)  # Column A
            is_details.write_blank(row, 1, None, bodydetailbold)  # Column B
            is_details.write_blank(row, 2, None, bodydetailbold)  # Column C
            is_details.write_blank(row, 3, None, bodydetailbold)  # Column C
            is_details.write(row, 4, "TOTAL", bodydetailbold)  # Column D (index 3)
            total_wages = sum(row[6] for row in detail_body_row)  # Sum of wages
            is_details.write(row, 5, round(total_wages, 2), bodydetailboldnetcurrency)
            
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
                is_details.write(row, col, detail_body[11].upper(), bodydetailnormalleft)  # SSS No
                col += 1
                is_details.write(row, col, detail_body[3], bodydetailbold)  # Hire Date
                col += 1
                is_details.write(row, col, detail_body[6], bodydetailnormalnetcurrency)  # SSS
                col += 1
                is_details.write(row, col, detail_body[7], bodydetailnormalnetcurrency)  # SSS WISP
                col += 1
                is_details.write(row, col, detail_body[8], bodydetailnormalnetcurrency)  # SSS EC Share
                col += 1
                is_details.write(row, col, detail_body[9], bodydetailnormalnetcurrency)  # SSS ER Share
                col += 1
                is_details.write(row, col, detail_body[10], bodydetailnormalnetcurrency)  # SSS Whisper
                col += 1
                
                # Increment row for the next employee
                row += 1
                
            # After the loop, write "TOTAL" in the cell below the last hire date row
            is_details.write_blank(row, 0, None, bodydetailbold)  # Column A
            is_details.write_blank(row, 1, None, bodydetailbold)  # Column B
            is_details.write_blank(row, 2, None, bodydetailbold)  # Column C
            is_details.write_blank(row, 3, None, bodydetailbold)  # Column C
            is_details.write(row, 4, "TOTAL", bodydetailbold)  # Column D (index 3)
            total_wages = sum(row[6] for row in detail_body_row)  # Sum of wages
            is_details.write(row, 5, round(total_wages, 2), bodydetailboldnetcurrency)
            
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
                is_details.write(row, col, detail_body[11].upper(), bodydetailnormalleft)  # SSS No
                col += 1
                is_details.write(row, col, detail_body[3], bodydetailbold)  # Hire Date
                col += 1
                is_details.write(row, col, detail_body[6], bodydetailnormalnetcurrency)  # SSS
                col += 1
                is_details.write(row, col, detail_body[7], bodydetailnormalnetcurrency)  # SSS WISP
                col += 1
                is_details.write(row, col, detail_body[8], bodydetailnormalnetcurrency)  # SSS EC Share
                col += 1
                is_details.write(row, col, detail_body[9], bodydetailnormalnetcurrency)  # SSS ER Share
                col += 1
                is_details.write(row, col, detail_body[10], bodydetailnormalnetcurrency)  # SSS Whisper
                col += 1
                
                # Increment row for the next employee
                row += 1
                
            # After the loop, write "TOTAL" in the cell below the last hire date row
            is_details.write_blank(row, 0, None, bodydetailbold)  # Column A
            is_details.write_blank(row, 1, None, bodydetailbold)  # Column B
            is_details.write_blank(row, 2, None, bodydetailbold)  # Column C
            is_details.write_blank(row, 3, None, bodydetailbold)  # Column C
            is_details.write(row, 4, "TOTAL", bodydetailbold)  # Column D (index 3)
            total_wages = sum(row[6] for row in detail_body_row)  # Sum of wages
            is_details.write(row, 5, round(total_wages, 2), bodydetailboldnetcurrency)                               
            
        # Set row height (optional)
        is_details.set_row(row, 15)
                    
        # Close Report
        workbook.close()
        output.seek(0)
        xy = output.read()
        
        file = base64.encodebytes(xy)  
        self.write({"excel_file": file})
        filename = 'sss_summary_report.xlsx'

        return {
            "type": "ir.actions.act_url",
            "url": f"/web/content/sss.report/{self.id}/excel_file/{filename}?download=true",
            "target": "self",
        }
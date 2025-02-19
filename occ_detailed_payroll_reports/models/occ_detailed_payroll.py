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
    _inherit = ['paycut.mixin']
    _description = 'Occ Detailed Payroll Report'

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
        selection=[(str(i), datetime(1900, i, 1).strftime('%B')) for i in range(1, 13)],
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
        
        subtotalboldcurrency = workbook.add_format(
            {
                "num_format": "#,##0.00",
                "align": "center",
                "valign": "vcenter",
                "text_wrap": True,
                "font": "Tahoma",
                "font_size": 10,
                "border": 1,
                "bold": True,
                "border_color": "black",
            }
        )
        
        departmentboldleft = workbook.add_format(
            {
                "align": "left",
                "valign": "bottom",
                "text_wrap": True,
                "font": "Tahoma",
                "font_size": 10,
                "font_color": "#21130d",
                'border': 1,
                "bold": True,
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
        emp_type = self.env["hr.employee.types"].search(
            domain=[
                ("for_payroll", "=", True),
            ]
            )
        is_details = False
        # print(f"EMP TYPE HERE: {emp_type}")
        for emp_types in emp_type:
            # Create a worksheet for each employee type
            print(f"EMP TYPE HERE: {emp_type}")
            is_details = workbook.add_worksheet(emp_types.name)
        
            # Set the worksheet tab color based on emp_type
            if emp_types.name == 'Regular':
                is_details.set_tab_color('#FF0000')  # Red for 'regular'
            elif emp_types.name == 'Probationary':
                is_details.set_tab_color('#8A2BE2')  # Violet for 'probationary'
            elif emp_types.name == 'Trainee':
                is_details.set_tab_color('#00B050')  # Green for 'probationary'
            elif emp_types.name == 'Consultant':
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
            is_details.write('B2', f"{emp_types.name} Payroll", headerformatbold)     
            is_details.write('B3', f"Attendance: {date_range}", headerformat) 
            is_details.write('B4', current_datetime, dateformat)            
            
            if emp_types.name == "Trainee":
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
            elif emp_types.name == "Consultant":
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
            elif emp_types.name == "Probitionary":
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
                    ("NET PAY", headerdetailboldnet)
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
            
            if emp_types.name == "Trainee":
                detail_body_query = f"""    
                SELECT 
                        ROW_NUMBER() OVER (ORDER BY he.name) AS row_num,               -- 0
                        he.name AS emp_name,                                           -- 1
                        hd.name->>'en_US' AS department,                               -- 2
                        TO_CHAR(he.joining_date, 'MM/DD/YYYY') AS hired_date,          -- 3
                        het.name AS emp_type,                                          -- 4
                        rc.name AS company,                                            -- 5
                        ROUND(hc.wage/2,2)::NUMERIC AS basic_sal,                      -- 6									  
                        ROUND(SUM(ep_wages_cte.wages),2)::NUMERIC AS wages,            -- 7
                        epd_wages_cte.epd_dedct AS absent_late_undertime,			   -- 8
                        epn_wages_cte.epn_ot AS overtime,							   -- 9
                        0.00 AS other_tax_income,									   -- 10
                        0.00 AS de_menimis,											   -- 11
                        0.00 AS retention_bonus,									   -- 12
                        ep.new_amount_nontaxable AS other_non_tax_income,			   -- 13
                        ROUND((hc.wage/2) + ep.new_amount_nontaxable + epn_wages_cte.epn_ot,2) AS gross_income, -- 14
                        ROUND(sss.ee_regular_amount::NUMERIC,2) AS sss,				   -- 15
                        0.00 AS sss_wisp,					    					   -- 16
                        ROUND(phic.er_amount::NUMERIC,2) AS phic,				       -- 17
                        ROUND(hdmf.ee_amount::NUMERIC,2) AS hdmf,					   -- 18
                        0.00 AS addnl_hdmf,							 	 		       -- 19
                        ep.amount_tax_signed AS wtx,					 	 		   -- 20
                        (epd_wages_cte.epd_dedct + sss.ee_regular_amount + phic.er_amount + hdmf.ee_amount + sss.ee_mpf_amount)  AS total_deduction,  -- 21
                        amount_total AS net_pay,									   -- 22
                        ROUND(sss.er_ec_amount::NUMERIC,2) AS sss_ec_share,			   -- 23
                        ROUND(sss.ee_regular_amount::NUMERIC,2) AS sss_er_share,	   -- 24
                        0.00 AS sss_whisper,						    			   -- 25
                        ROUND(phic.er_amount::NUMERIC,2) AS phic_er_share,	  		   -- 26
                        ROUND(hdmf.ee_amount::NUMERIC,2) AS hdmf_er_share			   -- 27
                FROM exhr_payslip ep
                LEFT JOIN hr_employee he ON he.id = ep.employee_id
                LEFT JOIN hr_department hd ON hd.id = he.department_id
                LEFT JOIN res_company rc ON rc.id = he.company_id
                LEFT JOIN hr_employee_types het ON het.id = he.employee_type_id
                LEFT JOIN hr_contract hc ON hc.employee_id = he.id AND hc.department_id = hd.id
                LEFT JOIN (
                                SELECT  
                                    (hc.wage / 2)::NUMERIC AS wages,
                                    ep.id AS payslip_id,
									ep.employee_id AS emp_id
                                FROM exhr_payslip ep
                                                        LEFT JOIN hr_contract hc ON hc.employee_id = ep.employee_id
                                WHERE hc.state = 'open'
                            ) ep_wages_cte ON ep_wages_cte.payslip_id = ep.id AND ep_wages_cte.emp_id = ep.employee_id
                LEFT JOIN (
                                                SELECT
                                                        ep.id AS payslip_id,
                                                        epd.amount_total AS epd_dedct,
                                                        ep.employee_id AS emp_id
                                FROM exhr_payslip ep
                                                        LEFT JOIN hr_contract hc ON hc.employee_id = ep.employee_id
                                                        LEFT JOIN exhr_payslip_deductions epd ON epd.payslip_id = ep.id 
                                WHERE hc.state = 'open'
                                                        AND epd.name_id ='6'
                            ) epd_wages_cte ON epd_wages_cte.payslip_id = ep.id AND epd_wages_cte.emp_id = ep.employee_id
                LEFT JOIN (
                                                SELECT
                                                        ep.id AS payslip_id,
                                                        epn.amount_subtotal AS epn_ot,
                                                        ep.employee_id AS emp_id
                                FROM exhr_payslip ep
                                                        LEFT JOIN hr_contract hc ON hc.employee_id = ep.employee_id
                                                        LEFT JOIN exhr_payslip_earnings epn ON epn.payslip_id = ep.id 
                                WHERE hc.state = 'open'
                                                        AND epn.name_id ='2'
                            ) epn_wages_cte ON epn_wages_cte.payslip_id = ep.id AND epn_wages_cte.emp_id = ep.employee_id
                LEFT JOIN sss_contribution_line sss ON sss.payslip_id = ep.id
                LEFT JOIN phic_contribution_line phic ON phic.payslip_id = ep.id
                LEFT JOIN hdmf_contribution_line hdmf ON hdmf.payslip_id = ep.id
                WHERE hc.state = 'open'
                AND rc.id = {self.multi_company_id.id}
                AND he.employee_type_id = {emp_types.id}
                AND ep.pay_period_from::DATE >= '{self.date_from}'
                AND ep.pay_period_to::DATE <= '{self.date_to}'
                
                GROUP BY he.name, hd.name, he.joining_date, het.name, rc.name, hc.wage, ep.new_amount_nontaxable, epd_wages_cte.epd_dedct,
                    sss.ee_regular_amount, epn_wages_cte.epn_ot, phic.er_amount, sss.er_ec_amount, ep.amount_tax_signed, hdmf.ee_amount, ep.amount_total,
                    sss.ee_mpf_amount;
                """
                params = (self.multi_company_id.id, emp_types.id, self.date_from, self.date_to)
            
                # Execute the query with parameters
                self._cr.execute(detail_body_query, params)
                detail_body_row = self._cr.fetchall()
                
            elif emp_types.name == "Consultant":
                detail_body_query = f"""
                SELECT 
                        ROW_NUMBER() OVER (ORDER BY he.name) AS row_num,               -- 0
                        he.name AS emp_name,                                           -- 1
                        hd.name->>'en_US' AS department,                               -- 2
                        TO_CHAR(he.joining_date, 'MM/DD/YYYY') AS hired_date,          -- 3
                        het.name AS emp_type,                                          -- 4
                        rc.name AS company,                                            -- 5
                        ROUND(hc.wage/2,2)::NUMERIC AS basic_sal,					   -- 6
                        ROUND(SUM(ep_wages_cte.wages),2)::NUMERIC AS wages,            -- 7
                        epd_wages_cte.epd_dedct AS absent_late_undertime,			   -- 8
                        epn_wages_cte.epn_ot AS overtime,							   -- 9
                        0.00 AS other_tax_income,									   -- 10
                        0.00 AS de_menimis,											   -- 11
                        0.00 AS retention_bonus,									   -- 12
                        ep.new_amount_nontaxable AS other_non_tax_income,			   -- 13
                        ROUND((hc.wage/2) + ep.new_amount_nontaxable + epn_wages_cte.epn_ot,2) AS gross_income, -- 14
                        ROUND(sss.ee_regular_amount::NUMERIC,2) AS sss,				   -- 15
                        0.00 AS sss_wisp,					    					   -- 16
                        ROUND(phic.er_amount::NUMERIC,2) AS phic,				       -- 17
                        ROUND(hdmf.ee_amount::NUMERIC,2) AS hdmf,					   -- 18
                        0.00 AS addnl_hdmf,							 	 		       -- 19
                        ep.amount_tax_signed AS wtx,					 	 		   -- 20
                        (epd_wages_cte.epd_dedct + sss.ee_regular_amount + phic.er_amount + hdmf.ee_amount + sss.ee_mpf_amount)  AS total_deduction,   -- 21
                        amount_total AS net_pay,									   -- 22
                        ROUND(sss.er_ec_amount::NUMERIC,2) AS sss_ec_share,			   -- 23
                        ROUND(sss.ee_regular_amount::NUMERIC,2) AS sss_er_share,	   -- 24
                        0.00 AS sss_whisper,						    			   -- 25
                        ROUND(phic.er_amount::NUMERIC,2) AS phic_er_share,	  		   -- 26
                        ROUND(hdmf.ee_amount::NUMERIC,2) AS hdmf_er_share,		       -- 27
						he.employee_id AS emp_id                                       -- 28
                FROM exhr_payslip ep
                LEFT JOIN hr_employee he ON he.id = ep.employee_id
                LEFT JOIN hr_department hd ON hd.id = he.department_id
                LEFT JOIN res_company rc ON rc.id = he.company_id
                LEFT JOIN hr_employee_types het ON het.id = he.employee_type_id
                LEFT JOIN hr_contract hc ON hc.employee_id = he.id AND hc.department_id = hd.id
                LEFT JOIN (
                                SELECT  
                                    (hc.wage / 2)::NUMERIC AS wages,
                                    ep.id AS payslip_id,
									ep.employee_id AS emp_id
                                FROM exhr_payslip ep
                                                        LEFT JOIN hr_contract hc ON hc.employee_id = ep.employee_id
                                WHERE hc.state = 'open'
                            ) ep_wages_cte ON ep_wages_cte.payslip_id = ep.id AND ep_wages_cte.emp_id = ep.employee_id
                LEFT JOIN (
                                                SELECT
                                                        ep.id AS payslip_id,
                                                        epd.amount_total AS epd_dedct,
                                                        ep.employee_id AS emp_id
                                FROM exhr_payslip ep
                                                        LEFT JOIN hr_contract hc ON hc.employee_id = ep.employee_id
                                                        LEFT JOIN exhr_payslip_deductions epd ON epd.payslip_id = ep.id 
                                WHERE hc.state = 'open'
                                                        AND epd.name_id ='6'
                            ) epd_wages_cte ON epd_wages_cte.payslip_id = ep.id AND epd_wages_cte.emp_id = ep.employee_id
                LEFT JOIN (
                                                SELECT
                                                        ep.id AS payslip_id,
                                                        epn.amount_subtotal AS epn_ot,
                                                        ep.employee_id AS emp_id
                                FROM exhr_payslip ep
                                                        LEFT JOIN hr_contract hc ON hc.employee_id = ep.employee_id
                                                        LEFT JOIN exhr_payslip_earnings epn ON epn.payslip_id = ep.id 
                                WHERE hc.state = 'open'
                                                        AND epn.name_id ='2'
                            ) epn_wages_cte ON epn_wages_cte.payslip_id = ep.id AND epn_wages_cte.emp_id = ep.employee_id
                LEFT JOIN sss_contribution_line sss ON sss.payslip_id = ep.id
                LEFT JOIN phic_contribution_line phic ON phic.payslip_id = ep.id
                LEFT JOIN hdmf_contribution_line hdmf ON hdmf.payslip_id = ep.id
                WHERE hc.state = 'open'
                AND rc.id = {self.multi_company_id.id}
                AND he.employee_type_id = {emp_types.id}
                AND ep.pay_period_from::DATE >= '{self.date_from}'
                AND ep.pay_period_to::DATE <= '{self.date_to}'
                
                GROUP BY he.name, hd.name, he.joining_date, het.name, rc.name, hc.wage, ep.new_amount_nontaxable, epd_wages_cte.epd_dedct,
                    sss.ee_regular_amount, epn_wages_cte.epn_ot, phic.er_amount, sss.er_ec_amount, ep.amount_tax_signed, hdmf.ee_amount, ep.amount_total,
                    sss.ee_mpf_amount, he.employee_id;
                """
                params = (self.multi_company_id.id, emp_types.id, self.date_from, self.date_to)
            
                # Execute the query with parameters
                self._cr.execute(detail_body_query, params)
                detail_body_row = self._cr.fetchall()
                
            elif emp_types.name == "Probitionary":
                detail_body_query = f"""
                SELECT 
                        ROW_NUMBER() OVER (ORDER BY he.name) AS row_num,               -- 0
                        he.name AS emp_name,                                           -- 1
                        hd.name->>'en_US' AS department,                               -- 2
                        TO_CHAR(he.joining_date, 'MM/DD/YYYY') AS hired_date,          -- 3
                        het.name AS emp_type,                                          -- 4
                        rc.name AS company,                                            -- 5
                        ROUND(hc.wage/2,2)::NUMERIC AS basic_sal,					   -- 6
                        ROUND(SUM(ep_wages_cte.wages),2)::NUMERIC AS wages,            -- 7
                        epd_wages_cte.epd_dedct AS absent_late_undertime,			   -- 8
                        epn_wages_cte.epn_ot AS overtime,							   -- 9
                        0.00 AS other_tax_income,									   -- 10
                        0.00 AS de_menimis,											   -- 11
                        0.00 AS retention_bonus,									   -- 12
                        ep.new_amount_nontaxable AS other_non_tax_income,			   -- 13
                        ROUND((hc.wage/2) + ep.new_amount_nontaxable + epn_wages_cte.epn_ot,2) AS gross_income, -- 14
                        ROUND(sss.ee_regular_amount::NUMERIC,2) AS sss,				   -- 15
                        0.00 AS sss_wisp,					    					   -- 16
                        ROUND(phic.er_amount::NUMERIC,2) AS phic,				       -- 17
                        ROUND(hdmf.ee_amount::NUMERIC,2) AS hdmf,					   -- 18
                        0.00 AS addnl_hdmf,							 	 		       -- 19
                        ep.amount_tax_signed AS wtx,					 	 		   -- 20
                        (epd_wages_cte.epd_dedct + sss.ee_regular_amount + phic.er_amount + hdmf.ee_amount + sss.ee_mpf_amount)  AS total_deduction,  -- 21
                        amount_total AS net_pay,									   -- 22
                        ROUND(sss.er_ec_amount::NUMERIC,2) AS sss_ec_share,			   -- 23
                        ROUND(sss.ee_regular_amount::NUMERIC,2) AS sss_er_share,	   -- 24
                        0.00 AS sss_whisper,						    			   -- 25
                        ROUND(phic.er_amount::NUMERIC,2) AS phic_er_share,	  		   -- 26
                        ROUND(hdmf.ee_amount::NUMERIC,2) AS hdmf_er_share			   -- 27
                FROM exhr_payslip ep
                LEFT JOIN hr_employee he ON he.id = ep.employee_id
                LEFT JOIN hr_department hd ON hd.id = he.department_id
                LEFT JOIN res_company rc ON rc.id = he.company_id
                LEFT JOIN hr_employee_types het ON het.id = he.employee_type_id
                LEFT JOIN hr_contract hc ON hc.employee_id = he.id AND hc.department_id = hd.id
                LEFT JOIN (
                                SELECT  
                                    (hc.wage / 2)::NUMERIC AS wages,
                                    ep.id AS payslip_id,
									ep.employee_id AS emp_id
                                FROM exhr_payslip ep
                                                        LEFT JOIN hr_contract hc ON hc.employee_id = ep.employee_id
                                WHERE hc.state = 'open'
                            ) ep_wages_cte ON ep_wages_cte.payslip_id = ep.id AND ep_wages_cte.emp_id = ep.employee_id
                LEFT JOIN (
                                                SELECT
                                                        ep.id AS payslip_id,
                                                        epd.amount_total AS epd_dedct,
                                                        ep.employee_id AS emp_id
                                FROM exhr_payslip ep
                                                        LEFT JOIN hr_contract hc ON hc.employee_id = ep.employee_id
                                                        LEFT JOIN exhr_payslip_deductions epd ON epd.payslip_id = ep.id 
                                WHERE hc.state = 'open'
                                                        AND epd.name_id ='6'
                            ) epd_wages_cte ON epd_wages_cte.payslip_id = ep.id AND epd_wages_cte.emp_id = ep.employee_id
                LEFT JOIN (
                                                SELECT
                                                        ep.id AS payslip_id,
                                                        epn.amount_subtotal AS epn_ot,
                                                        ep.employee_id AS emp_id
                                FROM exhr_payslip ep
                                                        LEFT JOIN hr_contract hc ON hc.employee_id = ep.employee_id
                                                        LEFT JOIN exhr_payslip_earnings epn ON epn.payslip_id = ep.id 
                                WHERE hc.state = 'open'
                                                        AND epn.name_id ='2'
                            ) epn_wages_cte ON epn_wages_cte.payslip_id = ep.id AND epn_wages_cte.emp_id = ep.employee_id
                LEFT JOIN sss_contribution_line sss ON sss.payslip_id = ep.id
                LEFT JOIN phic_contribution_line phic ON phic.payslip_id = ep.id
                LEFT JOIN hdmf_contribution_line hdmf ON hdmf.payslip_id = ep.id
                WHERE hc.state = 'open'
                AND rc.id = {self.multi_company_id.id}
                AND he.employee_type_id = {emp_types.id}
                AND ep.pay_period_from::DATE >= '{self.date_from}'
                AND ep.pay_period_to::DATE <= '{self.date_to}'
                
                GROUP BY he.name, hd.name, he.joining_date, het.name, rc.name, hc.wage, ep.new_amount_nontaxable, epd_wages_cte.epd_dedct,
                    sss.ee_regular_amount, epn_wages_cte.epn_ot, phic.er_amount, sss.er_ec_amount, ep.amount_tax_signed, hdmf.ee_amount, ep.amount_total,
                    sss.ee_mpf_amount;
                """
                params = (self.multi_company_id.id, emp_types.id, self.date_from, self.date_to)
            
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
                        ROUND(hc.wage/2,2)::NUMERIC AS basic_sal,					   -- 6
                        ROUND(SUM(ep_wages_cte.wages),2)::NUMERIC AS wages,            -- 7
                        epd_wages_cte.epd_dedct AS absent_late_undertime,			   -- 8
                        epn_wages_cte.epn_ot AS overtime,							   -- 9
                        0.00 AS other_tax_income,									   -- 10
                        0.00 AS de_menimis,											   -- 11
                        0.00 AS retention_bonus,									   -- 12
                        ep.new_amount_nontaxable AS other_non_tax_income,			   -- 13
                        ROUND((hc.wage/2) + ep.new_amount_nontaxable + epn_wages_cte.epn_ot,2) AS gross_income, -- 14
                        ROUND(sss.ee_regular_amount::NUMERIC,2) AS sss,				   -- 15
                        0.00 AS sss_wisp,					    					   -- 16
                        ROUND(phic.er_amount::NUMERIC,2) AS phic,				       -- 17
                        ROUND(hdmf.ee_amount::NUMERIC,2) AS hdmf,					   -- 18
                        0.00 AS addnl_hdmf,							 	 		       -- 19
                        ep.amount_tax_signed AS wtx,					 	 		   -- 20
                        (epd_wages_cte.epd_dedct + sss.ee_regular_amount + phic.er_amount + hdmf.ee_amount + sss.ee_mpf_amount)  AS total_deduction,   -- 21
                        amount_total AS net_pay,									   -- 22
                        ROUND(sss.er_ec_amount::NUMERIC,2) AS sss_ec_share,			   -- 23
                        ROUND(sss.ee_regular_amount::NUMERIC,2) AS sss_er_share,	   -- 24
                        0.00 AS sss_whisper,						    			   -- 25
                        ROUND(phic.er_amount::NUMERIC,2) AS phic_er_share,	  		   -- 26
                        ROUND(hdmf.ee_amount::NUMERIC,2) AS hdmf_er_share			   -- 27
                FROM exhr_payslip ep
                LEFT JOIN hr_employee he ON he.id = ep.employee_id
                LEFT JOIN hr_department hd ON hd.id = he.department_id
                LEFT JOIN res_company rc ON rc.id = he.company_id
                LEFT JOIN hr_employee_types het ON het.id = he.employee_type_id
                LEFT JOIN hr_contract hc ON hc.employee_id = he.id AND hc.department_id = hd.id
                LEFT JOIN (
                                SELECT  
                                    (hc.wage / 2)::NUMERIC AS wages,
                                    ep.id AS payslip_id,
									ep.employee_id AS emp_id
                                FROM exhr_payslip ep
                                                        LEFT JOIN hr_contract hc ON hc.employee_id = ep.employee_id
                                WHERE hc.state = 'open'
                            ) ep_wages_cte ON ep_wages_cte.payslip_id = ep.id AND ep_wages_cte.emp_id = ep.employee_id
                LEFT JOIN (
                                                SELECT
                                                        ep.id AS payslip_id,
                                                        epd.amount_total AS epd_dedct,
                                                        ep.employee_id AS emp_id
                                FROM exhr_payslip ep
                                                        LEFT JOIN hr_contract hc ON hc.employee_id = ep.employee_id
                                                        LEFT JOIN exhr_payslip_deductions epd ON epd.payslip_id = ep.id 
                                WHERE hc.state = 'open'
                                                        AND epd.name_id ='6'
                            ) epd_wages_cte ON epd_wages_cte.payslip_id = ep.id AND epd_wages_cte.emp_id = ep.employee_id
                LEFT JOIN (
                                                SELECT
                                                        ep.id AS payslip_id,
                                                        epn.amount_subtotal AS epn_ot,
                                                        ep.employee_id AS emp_id
                                FROM exhr_payslip ep
                                                        LEFT JOIN hr_contract hc ON hc.employee_id = ep.employee_id
                                                        LEFT JOIN exhr_payslip_earnings epn ON epn.payslip_id = ep.id 
                                WHERE hc.state = 'open'
                                                        AND epn.name_id ='2'
                            ) epn_wages_cte ON epn_wages_cte.payslip_id = ep.id AND epn_wages_cte.emp_id = ep.employee_id
                LEFT JOIN sss_contribution_line sss ON sss.payslip_id = ep.id
                LEFT JOIN phic_contribution_line phic ON phic.payslip_id = ep.id
                LEFT JOIN hdmf_contribution_line hdmf ON hdmf.payslip_id = ep.id
                WHERE hc.state = 'open'
                AND rc.id = {self.multi_company_id.id}
                AND he.employee_type_id = {emp_types.id}
                AND ep.pay_period_from::DATE >= '{self.date_from}'
                AND ep.pay_period_to::DATE <= '{self.date_to}'
                
                GROUP BY he.name, hd.name, he.joining_date, het.name, rc.name, hc.wage, ep.new_amount_nontaxable, epd_wages_cte.epd_dedct,
                    sss.ee_regular_amount, epn_wages_cte.epn_ot, phic.er_amount, sss.er_ec_amount, ep.amount_tax_signed, hdmf.ee_amount, ep.amount_total,
                    sss.ee_mpf_amount;
                """
                params = (self.multi_company_id.id, emp_types.id, self.date_from, self.date_to)
                
                # Execute the query with parameters
                self._cr.execute(detail_body_query, params)
                detail_body_row = self._cr.fetchall()
            
            # Write the detail rows starting from row 6 (the next row after headers)
            row = 6  # Start from row 6, just below the headers
            
            if emp_types.name == "Trainee":
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
                
            elif emp_types.name == "Consultant":
                # Fetch employee details grouped by department
                departments = {}
                for detail_body in detail_body_row:
                    department_name = detail_body[2] if len(detail_body) > 27 else "No Department"
                    if department_name not in departments:
                        departments[department_name] = []
                    departments[department_name].append(detail_body)
                    
                total_wages = 0
                total_absent_late = 0
                total_overtime = 0
                total_other_tax_income = 0
                total_de_minimis = 0
                total_retention_bonus = 0
                total_other_non_tax_income = 0
                total_gross_income = 0
                total_sss = 0
                total_sss_wisp = 0
                total_phic = 0
                total_hdmf = 0
                total_additional_hdmf = 0
                total_wtx = 0
                total_total_deduction = 0
                total_net_pay = 0

                # Write department headers and employee details
                for department_name, employees in departments.items():
                    # Initialize department-level totals

                    # Write the department header
                    is_details.write(row, 1, f"Department: {department_name.upper()}", departmentboldleft)  # Department name in column B
                    row += 1  # Move to the next row after the department header
                    
                    subtotal_wages = 0
                    subtotal_absent_late = 0
                    subtotal_overtime = 0
                    subtotal_other_tax_income = 0
                    subtotal_de_minimis = 0
                    subtotal_retention_bonus = 0
                    subtotal_other_non_tax_income = 0
                    subtotal_gross_income = 0
                    subtotal_sss = 0
                    subtotal_sss_wisp = 0
                    subtotal_phic = 0
                    subtotal_hdmf = 0
                    subtotal_additional_hdmf = 0
                    subtotal_wtx = 0
                    subtotal_total_deduction = 0
                    subtotal_net_pay = 0

                    for detail_body in employees:
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
                        subtotal_wages += basic_salary
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

                        # Increment row for the next employee
                        row += 1
                    
                    # After writing all employees, write Subtotal for the department
                    is_details.write(row, 3, "Subtotal", bodydetailbold)  # "Subtotal" label in column D
                    is_details.write(row, 4, round(subtotal_wages, 2), subtotalboldcurrency)  # Wages subtotal
                    is_details.write(row, 5, round(subtotal_absent_late, 2), subtotalboldcurrency)  # Absent/late subtotal
                    is_details.write(row, 6, round(subtotal_overtime, 2), subtotalboldcurrency)  # Overtime subtotal
                    is_details.write(row, 7, round(subtotal_other_tax_income, 2), subtotalboldcurrency)  # Other tax income subtotal
                    is_details.write(row, 8, round(subtotal_de_minimis, 2), subtotalboldcurrency)  # De minimis subtotal
                    is_details.write(row, 9, round(subtotal_retention_bonus, 2), subtotalboldcurrency)  # Retention bonus subtotal
                    is_details.write(row, 10, round(subtotal_other_non_tax_income, 2), subtotalboldcurrency)  # Other non-tax income subtotal
                    is_details.write(row, 11, round(subtotal_gross_income, 2), subtotalboldcurrency)  # Gross income subtotal
                    is_details.write(row, 12, round(subtotal_sss, 2), subtotalboldcurrency)  # SSS subtotal
                    is_details.write(row, 13, round(subtotal_sss_wisp, 2), subtotalboldcurrency)  # SSS WISP subtotal
                    is_details.write(row, 14, round(subtotal_phic, 2), subtotalboldcurrency)  # PHIC subtotal
                    is_details.write(row, 15, round(subtotal_hdmf, 2), subtotalboldcurrency)  # HDMF subtotal
                    is_details.write(row, 16, round(subtotal_additional_hdmf, 2), subtotalboldcurrency)  # Additional HDMF subtotal
                    is_details.write(row, 17, round(subtotal_wtx, 2), subtotalboldcurrency)  # WTX subtotal
                    is_details.write(row, 18, round(subtotal_total_deduction, 2), subtotalboldcurrency)  # Total deduction subtotal
                    is_details.write(row, 19, round(subtotal_net_pay, 2), subtotalboldcurrency)  # Net pay subtotal

                    # Move to the next row
                    row += 1

                    
                    # Add department subtotal to the total wages
                    total_wages += subtotal_wages
                    total_absent_late += subtotal_absent_late
                    total_overtime += subtotal_overtime
                    total_other_tax_income += subtotal_other_tax_income
                    total_de_minimis += subtotal_de_minimis
                    total_retention_bonus += subtotal_retention_bonus
                    total_other_non_tax_income += subtotal_other_non_tax_income
                    total_gross_income += subtotal_gross_income
                    total_sss += subtotal_sss
                    total_sss_wisp += subtotal_sss_wisp
                    total_phic += subtotal_phic
                    total_hdmf += subtotal_hdmf
                    total_additional_hdmf += subtotal_additional_hdmf
                    total_wtx += subtotal_wtx
                    total_total_deduction += subtotal_total_deduction
                    total_net_pay += subtotal_net_pay
                    
                # After the loop, write "TOTAL" in the cell below the last hire date row
                is_details.write(row, 3, "TOTAL", bodydetailbold)  # Column D (index 3)
                is_details.write(row, 4, round(total_wages, 2), bodydetailboldnetcurrency)  # Grand total wages
                is_details.write(row, 5, round(total_absent_late, 2), bodydetailboldnetcurrency)  # Grand total absent/late
                is_details.write(row, 6, round(total_overtime, 2), bodydetailboldnetcurrency)  # Grand total overtime
                is_details.write(row, 7, round(total_other_tax_income, 2), bodydetailboldnetcurrency)  # Grand total other tax income
                is_details.write(row, 8, round(total_de_minimis, 2), bodydetailboldnetcurrency)  # Grand total de minimis
                is_details.write(row, 9, round(total_retention_bonus, 2), bodydetailboldnetcurrency)  # Grand total retention bonus
                is_details.write(row, 10, round(total_other_non_tax_income, 2), bodydetailboldnetcurrency)  # Grand total other non-tax income
                is_details.write(row, 11, round(total_gross_income, 2), bodydetailboldnetcurrency)  # Grand total gross income
                is_details.write(row, 12, round(total_sss, 2), bodydetailboldnetcurrency)  # Grand total SSS
                is_details.write(row, 13, round(total_sss_wisp, 2), bodydetailboldnetcurrency)  # Grand total SSS WISP
                is_details.write(row, 14, round(total_phic, 2), bodydetailboldnetcurrency)  # Grand total PHIC
                is_details.write(row, 15, round(total_hdmf, 2), bodydetailboldnetcurrency)  # Grand total HDMF
                is_details.write(row, 16, round(total_additional_hdmf, 2), bodydetailboldnetcurrency)  # Grand total additional HDMF
                is_details.write(row, 17, round(total_wtx, 2), bodydetailboldnetcurrency)  # Grand total WTX
                is_details.write(row, 18, round(total_total_deduction, 2), bodydetailboldnetcurrency)  # Grand total deductions
                is_details.write(row, 19, round(total_net_pay, 2), bodydetailboldnetcurrency)  # Grand total net pay

            elif emp_types.name == "Probitionary":
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
                total_wages = sum(row[6] for row in detail_body_row)  # Sum of wages
                is_details.write(row, 4, round(total_wages, 2), bodydetailboldnetcurrency)
                total_absent_late = sum(row[8] if row[8] is not None else 0 for row in detail_body_row)  # Sum of absent/late
                is_details.write(row, 5, round(total_absent_late, 2), bodydetailboldnetcurrency)  # Grand total absent/late
                total_overtime = sum(row[9] for row in detail_body_row)  # Sum of overtime
                is_details.write(row, 6, round(total_overtime, 2), bodydetailboldnetcurrency)  # Grand total overtime
                total_other_tax_income = sum(row[10] for row in detail_body_row)  # Sum of other tax income
                is_details.write(row, 7, round(total_other_tax_income, 2), bodydetailboldnetcurrency)  # Grand total other tax income
                total_de_minimis = sum(row[11] for row in detail_body_row)  # Sum of de minimis
                is_details.write(row, 8, round(total_de_minimis, 2), bodydetailboldnetcurrency)  # Grand total de minimis
                total_retention_bonus = sum(row[12] for row in detail_body_row)  # Sum of retention bonus
                is_details.write(row, 9, round(total_retention_bonus, 2), bodydetailboldnetcurrency)  # Grand total retention bonus
                total_other_non_tax_income = sum(row[13] for row in detail_body_row)  # Sum of Other Non-Tax Income
                is_details.write(row, 10, round(total_other_non_tax_income, 2), bodydetailboldnetcurrency)  # Grand Other Non-Tax Income
                total_gross_income = sum(row[14] for row in detail_body_row)  # Sum of Gross Income
                is_details.write(row, 11, round(total_gross_income, 2), bodydetailboldnetcurrency)  # Grand Gross Income
                total_sss = sum(row[15] for row in detail_body_row)  # Sum of SSS
                is_details.write(row, 12, round(total_sss, 2), bodydetailboldnetcurrency)  # Grand total SSS
                total_sss_wispher = sum(row[16] for row in detail_body_row)  # Sum of SSS Whisper
                is_details.write(row, 13, round(total_sss_wispher, 2), bodydetailboldnetcurrency)  # Grand total SSS Whisper
                total_phic = sum(row[17] for row in detail_body_row)  # Sum of PHIC
                is_details.write(row, 14, round(total_phic, 2), bodydetailboldnetcurrency)  # Grand total PHIC
                total_hdmf = sum(row[18] for row in detail_body_row)  # Sum of HDMF
                is_details.write(row, 15, round(total_hdmf, 2), bodydetailboldnetcurrency)  # Grand total HDMF
                total_add_hdmf = sum(row[19] for row in detail_body_row)  # Sum of HDMF
                is_details.write(row, 16, round(total_add_hdmf, 2), bodydetailboldnetcurrency)  # Grand total HDMF
                total_wtx = sum(row[20] for row in detail_body_row)  # Sum of WTX
                is_details.write(row, 17, round(total_wtx, 2), bodydetailboldnetcurrency)  # Grand total WTX
                total_deduction = sum(row[21] if row[21] is not None else 0 for row in detail_body_row)  # Sum of Deduction
                is_details.write(row, 18, round(total_deduction, 2), bodydetailboldnetcurrency)  # Grand total Deduction
                total_net_pay = sum(row[22] for row in detail_body_row)  # Sum of net pay
                is_details.write(row, 19, round(total_net_pay, 2), bodydetailboldnetcurrency)  # Grand total net pay
                total_sss_ec_share = sum(row[23] for row in detail_body_row)  # Sum of SSS EC Share
                is_details.write(row, 20, round(total_sss_ec_share, 2), bodydetailboldnetcurrency)  # Grand total SSS EC Share
                total_sss_er_share = sum(row[24] for row in detail_body_row)  # Sum of SSS ER Share
                is_details.write(row, 21, round(total_sss_er_share, 2), bodydetailboldnetcurrency)  # Grand total SSS ER Share
                total_sss_whisper = sum(row[25] for row in detail_body_row)  # Sum of SSS Whisper
                is_details.write(row, 22, round(total_sss_whisper, 2), bodydetailboldnetcurrency)  # Grand total SSS Whisper
                total_phic_er_share = sum(row[26] for row in detail_body_row)  # Sum of PHIC ER Share
                is_details.write(row, 23, round(total_phic_er_share, 2), bodydetailboldnetcurrency)  # Grand total PHIC ER Share 
                total_hdmf_er_share= sum(row[27] for row in detail_body_row)  # Sum of HDMF ER Share
                is_details.write(row, 24, round(total_hdmf_er_share, 2), bodydetailboldnetcurrency)  # Grand total HDMF ER Share                            
                
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
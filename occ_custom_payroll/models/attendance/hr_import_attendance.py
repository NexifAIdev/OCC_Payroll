# -*- coding: utf-8 -*-
# Native Python modules
from datetime import datetime, date, time, timedelta

# Local python modules

# Custom python modules
import io, base64, pytz, xlsxwriter
import pylightxl as xl
from pytz import timezone
# from xlrd import open_workbook
from xlsxwriter.utility import xl_rowcol_to_cell_fast as rc

# Odoo modules
from odoo import models, fields, api, _
from odoo.tools.translate import _
from odoo.exceptions import UserError, ValidationError


class HRImportAttendance(models.Model):
    _name = "hr.import.attendance"
    _inherit = ["occ.payroll.cfg", "mail.thread"]
    _description = "Employee Attendance Sheet"
    _order = "create_date desc"

    def excel_download(self):
        name = self.env["hr.employee"].search([("user_id", "=", self.env.uid)], limit=1)

        employee_name = name.name if name else "You don't have an employee file in Odoo"

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output)
        summary = workbook.add_worksheet("Sheet")

        summary.freeze_panes(1, 1)
        summary.set_column("A:C", 20)
        summary.set_column("D:ZZ", 20)

        col = 0
        row = 0

        if self.upload_type == "a":
            header = [
                "User",
                "Start Date (MM,DD,YYYY)",
                "Start Time (h:mm AM/PM)",
                "End Date (MM,DD,YYYY)",
                "End Time (h:mm AM/PM)",
            ]
            title = "Clockify"
        else:
            header = ["Name", "Date (m/d/yyyy)", "Time IN (h:mm)", "Time OUT (h:mm)"]
            title = "Biometrics"

        summary.write_row(row, col, header)
        row += 1  # ✅ Fixed incorrect increment
        summary.write(row, col, employee_name)

        workbook.close()
        output.seek(0)

        # ✅ Fixed: Use `b64encode()` instead of `encodestring()`
        file = base64.b64encode(output.read()).decode("utf-8")

        self.write({"excel_file": file})

        # ✅ Fix URL formatting (ensure correct ordering)
        button = {
            "type": "ir.actions.act_url",
            "url": "/web/content/%s/%s/excel_file/%s (%s).xlsx?download=true"
            % (self._name, self.id, self._description, title),
            "target": "self",
        }
        return button

    name = fields.Char(string="Name", readonly=True, default="New", copy=False)
    data = fields.Binary(sring="Excel File", copy=False)
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("upload", "Uploaded"),
            ("validated", "Validated"),
            ("cancel", "Cancelled"),
        ],
        default="draft",
        string="Status",
        copy=False,
    )

    upload_type = fields.Selection(
        [("a", "CLOCKIFY"), ("b", "BIOMETRICS")], string="Type", required=True
    )
    excel_file = fields.Binary(string="Excel File")

    line_ids = fields.One2many(
        "hr.import.attendance.line", "employee_attendance_id", copy=False
    )
    attendance_lines_ids = fields.One2many(
        "employee.attendance.line", "employee_attendance_id", copy=False
    )

    def validate_button(self):
        for rec in self:
            if rec.state == "upload":
                rec.filter_data()
                rec._create_attendance_sheet()
            else:
                raise UserError(_("Not Valid"))
            rec.state = "validated"

    def cancel_button(self):
        if self.state == "upload":
            self.state = "cancel"

    def import_file(self):
        if self.name == "New":
            self.name = self.env["ir.sequence"].next_by_code(
                "import_attendance_no_sequence"
            )

        if self.upload_type == "a":
            self.import_clockify()
        elif self.upload_type == "b":
            pass
            # self.import_biometrics()
        else:
            raise UserError(_("Select Upload Type"))

        self.state = "upload"

    def import_biometrics(self):
        # Step 1: Delete Existing Records for the Current Attendance ID
        delete_query = """DELETE FROM import_employee_attendance_line WHERE employee_attendance_id = %s;""" % (self.id)
        self._cr.execute(delete_query)

        # Step 2: Check if File Exists
        if not self.data:
            raise UserError(_("No file to generate"))

        # Step 3: Decode Base64 Encoded Excel File
        fileobj = base64.b64decode(self.data)

        # Step 4: Read Excel File Using `pylightxl`
        db = xl.readxl(fileobj)

        # Step 5: Get the First Sheet and Read Rows
        sheet_name = db.ws_names[0]  # Get the first sheet name
        sheet = db.ws(sheet_name)  # Load the sheet

        # Step 6: Iterate Over Rows (Skipping Header)
        for row_idx in range(2, sheet.maxrow + 1):  # `pylightxl` is 1-based index
            try:
                employee_name = sheet.index(row_idx, 1)
                excel_date = sheet.index(row_idx, 2)  # Assuming it's in column B (2nd col)

                # Convert Excel Serial Date to Python Date
                try:
                    python_date = datetime(1899, 12, 30) + timedelta(days=float(excel_date))
                except ValueError:
                    python_date = None

                # Get Hour From and Hour To
                try:
                    date_from = float(sheet.index(row_idx, 2)) + float(sheet.index(row_idx, 3))
                    date_to = float(sheet.index(row_idx, 2)) + float(sheet.index(row_idx, 4))

                    python_date_from = datetime(1899, 12, 30) + timedelta(days=date_from)
                    python_date_to = datetime(1899, 12, 30) + timedelta(days=date_to)
                except ValueError:
                    python_date_from, python_date_to = None, None

                # Step 7: Search for Employee by Name
                search_employee_query = """SELECT id FROM hr_employee WHERE name = %s LIMIT 1"""
                self._cr.execute(search_employee_query, (employee_name,))
                search_employee_data = self._cr.fetchone()

                employee_id = search_employee_data[0] if search_employee_data else False

                # Step 8: Create Attendance Record
                self.env["hr.import.attendance.line"].create({
                    "employee_id": employee_id,
                    "name": employee_name,
                    "date_from": python_date.date() if python_date else None,
                    "hour_from": str(python_date_from.time()) if python_date_from else None,
                    "date_to": python_date.date() if python_date else None,
                    "hour_to": str(python_date_to.time()) if python_date_to else None,
                    "employee_attendance_id": self._origin.id,
                    "datestamp_from": str(python_date_from) if python_date_from else None,
                    "datestamp_to": str(python_date_to) if python_date_to else None,
                })

            except Exception as e:
                pass

    def import_clockify(self):
        # Step 1: Delete Existing Records for the Current Attendance ID
        delete_query = """DELETE FROM import_employee_attendance_line WHERE employee_attendance_id = %s;"""
        self._cr.execute(delete_query, (self.id,))

        # Step 2: Check if File Exists
        if not self.data:
            raise UserError(_("No file to generate"))

        # Step 3: Decode Base64 Encoded Excel File
        fileobj = base64.b64decode(self.data)

        # Step 4: Read Excel File Using `pylightxl`
        db = xl.readxl(fileobj)

        # Step 5: Get the First Sheet and Read Rows
        sheet_name = db.ws_names[0]  # Get the first sheet name
        sheet = db.ws(sheet_name)  # Load the sheet

        # Step 6: Iterate Over Rows (Skipping Header)
        for row_idx in range(2, sheet.maxrow + 1):  # `pylightxl` is 1-based index
            try:
                employee_name = sheet.index(row_idx, 1)
                date_from_excel = sheet.index(row_idx, 2)
                date_to_excel = sheet.index(row_idx, 4)

                # Convert Excel Serial Date to Python Date
                try:
                    date_from = datetime(1899, 12, 30) + timedelta(days=float(date_from_excel))
                    date_to = datetime(1899, 12, 30) + timedelta(days=float(date_to_excel))
                except ValueError:
                    date_from, date_to = None, None

                # Extract Hours and Minutes from Time Columns
                try:
                    hour_from_sec = int(float(sheet.index(row_idx, 3)) * 24 * 3600)
                    hour_from = time(hour_from_sec // 3600, (hour_from_sec % 3600) // 60)
                except:
                    hour_from = time(0, 0, 0)  # Default to 00:00:00

                try:
                    hour_to_sec = int(float(sheet.index(row_idx, 5)) * 24 * 3600)
                    hour_to = time(hour_to_sec // 3600, (hour_to_sec % 3600) // 60)
                except:
                    hour_to = time(0, 0, 0)  # Default to 00:00:00

                # Step 7: Search for Employee by Name
                search_employee_query = """SELECT id FROM hr_employee WHERE name = %s LIMIT 1"""
                self._cr.execute(search_employee_query, (employee_name,))
                search_employee_data = self._cr.fetchone()

                employee_id = search_employee_data[0] if search_employee_data else False

                # Step 8: Create Attendance Record
                self.env["hr.import.attendance.line"].create({
                    "employee_id": employee_id,
                    "name": employee_name,
                    "date_from": date_from.date() if date_from else None,
                    "hour_from": str(hour_from),
                    "date_to": date_to.date() if date_to else None,
                    "hour_to": str(hour_to),
                    "employee_attendance_id": self._origin.id,
                    "datestamp_from": f"{date_from.date()} {hour_from}" if date_from else None,
                    "datestamp_to": f"{date_to.date()} {hour_to}" if date_to else None,
                })

            except Exception as e:
                pass

    def filter_data(self):
        for data in self.line_ids:
            if data:
                if (
                    data.date_from == ""
                    or data.date_to == ""
                    or data.hour_from == "00:00:00"
                    or data.hour_to == "00:00:00"
                ):
                    if (
                        data.date_from != ""
                        and data.hour_from != "00:00:00"
                        and data.date_to != ""
                    ):
                        if data.date_from == data.date_to:
                            status = "IN"
                        else:
                            status = "BOTH"
                        # print("IF 0", "\nDATE FROM:",data.date_from , "\nHOUR FROM:",data.hour_from, "\nDATE TO:",data.date_to , "\nHOUR TO:",data.hour_to, "\nSTATUS:", status, "\n===========")
                        self._create_hr_attendance(
                            employee_data=data.employee_id,
                            datefrom=data.date_from,
                            dateto=data.date_to,
                            full_datefrom=data.datestamp_from,
                            full_dateto=data.datestamp_to,
                            status=status,
                        )
                    elif data.date_from != "" and data.hour_from != "00:00:00":
                        status = "IN"
                        self._create_hr_attendance(
                            employee_data=data.employee_id,
                            datefrom=data.date_from,
                            dateto=data.date_to,
                            full_datefrom=data.datestamp_from,
                            full_dateto=data.datestamp_to,
                            status=status,
                        )
                    # elif data.date_to != "" and data.hour_to != "00:00:00":
                    # 	status = "OUT"
                    # 	print("ELIF 1","\nDATE TO:",data.date_to , "\nHOUR TO:",data.hour_to, "\nSTATUS:", status, "\n===========")
                    # 	self._create_hr_attendance(
                    # 		employee_data=data.employee_id,
                    # 		datefrom=data.date_from,
                    # 		dateto=data.date_to,
                    # 		full_datefrom=data.datestamp_from,
                    # 		full_dateto=data.datestamp_to,
                    # 		status=status
                    # 	)
                    else:
                        status = "ELSE"
                        # print("NO","\nELSE", "\nDATE FROM:",data.date_from , "\nHOUR FROM:",data.hour_from, "\nDATE TO:",data.date_to , "\nHOUR TO:",data.hour_to, "\nSTATUS:", status, "\n===========")
                        create_missing_line = self.env[
                            "employee.attendance.line"
                        ].create(
                            {
                                "employee_id": data.employee_id.id,
                                "name": data.name,
                                "date_from": data.date_from,
                                "hour_from": data.hour_from,
                                "date_to": data.date_to,
                                "hour_to": data.hour_to,
                                "datestamp_from": data.datestamp_from,
                                "datestamp_to": data.datestamp_to,
                                "employee_attendance_id": data.employee_attendance_id.id,
                                "import_attendance_line_id": data._origin.id,
                            }
                        )
                else:
                    status = "BOTH"
                    # print("BOTH","\nELSE", "\nDATE FROM:",data.date_from , "\nHOUR FROM:",data.hour_from, "\nDATE TO:",data.date_to , "\nHOUR TO:",data.hour_to, "\nSTATUS:", status, "\n===========")
                    self._create_hr_attendance(
                        employee_data=data.employee_id,
                        datefrom=data.date_from,
                        dateto=data.date_to,
                        full_datefrom=data.datestamp_from,
                        full_dateto=data.datestamp_to,
                        status=status,
                    )
                    # print( "DATE FROM",data.date_from , "\nHOUR FROM" , data.hour_from , "  \nDATE TO" , data.date_to , "  \nHOUR TO", data.hour_to )

    def _create_hr_attendance(
        self, employee_data, datefrom, dateto, full_datefrom, full_dateto, status
    ):
        # print("STATUS:",status)
        if self.upload_type == "a":
            timestamp = "%m,%d,%Y %H:%M:%S"
            datestamp = "%m,%d,%Y"
        else:
            timestamp = "%Y-%m-%d %H:%M:%S"
            datestamp = "%Y-%m-%d"

        check_in = datetime.strptime(full_datefrom, timestamp) - timedelta(
            hours=8, minutes=00
        )
        if status != "IN":
            check_out = datetime.strptime(full_dateto, timestamp) - timedelta(
                hours=8, minutes=00
            )
        check_out_date = datetime.strptime(datefrom, datestamp)
        # print(check_out_date)
        # print(employee_data.name, check_in)
        # if status != "IN":
        # print(check_out,"\n================")

        # print(employee_data.id,"HEY")
        # print(employee_data.name, check_in)
        if employee_data.id:
            if employee_data.id == False:
                employee = False
            else:
                employee = employee_data.id

            query = """
				SELECT
					ha."id",
					ha.check_in,
					ha.check_out
				FROM hr_attendance ha
				WHERE ha.employee_id = %s
				AND ha.check_in_date::DATE = '%s'::DATE
				LIMIT 1
			""" % (
                employee,
                full_datefrom,
            )
            # print(query)
            self._cr.execute(query)
            query_data = self._cr.fetchall()
            if not query_data:

                if status == "BOTH":
                    # print("CREATE NEW ATTENDANCE BOTH\n",check_in,"\n-----------")
                    self.env["hr.attendance"].sudo().create(
                        {
                            "employee_id": employee,
                            "check_in": check_in,
                            "check_out": check_out,
                            "check_in_date": check_out_date,
                            "import_code": self.name,
                        }
                    )

                if status == "IN":
                    # print("CREATE NEW ATTENDANCE INN\n",check_in,"\n-----------")
                    insert = """
						INSERT INTO "hr_attendance"
						(
							/*00*/ "employee_id",
							/*01*/ "check_in",
							/*02*/ "worked_hours",
							/*03*/ "create_uid",
							/*04*/ "create_date",
							/*05*/ "check_in_date",
							/*06*/ "pushed_to_sheet",
							/*07*/ "import_code"
						) VALUES
						(
							/*00*/ %s,
							/*01*/ '%s'::TIMESTAMP,
							/*02*/ 0,
							/*03*/ %s,
							/*04*/ NOW()::TIMESTAMP,
							/*05*/ '%s'::DATE,
							/*06*/ 'f',
							/*07*/ '%s'
						); """ % (
                        employee,  # 00
                        check_in,  # 01
                        self.env.uid,  # 03
                        check_out_date,  # 05
                        self.name,  # 07
                    )
                    self._cr.execute(insert)

                    """self.env['hr.attendance'].sudo().create({
						'employee_id' : employee,
						'check_in' : check_in,
						'check_out' : False,
						'check_in_date' : check_out_date,
						'import_code' : self.name,})"""

            if query_data:
                for att in query_data:

                    if status in ("IN", "BOTH"):
                        if att[1]:
                            att_check_in = datetime.strptime(
                                str(att[1]), "%Y-%m-%d %H:%M:%S"
                            )
                            if att_check_in > check_in:
                                self.env["hr.attendance"].search(
                                    [("id", "=", att[0])]
                                ).sudo().write({"check_in": check_in})

                    if status in ("OUT", "BOTH"):
                        if att[2]:
                            att_check_out = datetime.strptime(
                                str(att[2]), "%Y-%m-%d %H:%M:%S"
                            )
                            if att_check_out < check_out:
                                self.env["hr.attendance"].search(
                                    [("id", "=", att[0])]
                                ).sudo().write({"check_out": check_out})

    def _create_attendance_sheet(self):
        query = """
			SELECT
				ha.employee_id,
				ha.check_in_date
			FROM hr_attendance ha
			WHERE ha.import_code = '%s'
		""" % (
            self.name
        )
        self._cr.execute(query)
        query_data = self._cr.fetchall()
        if query_data:
            for data in query_data:
                sheet = self.env["hr.attendance.sheet"].search(
                    [
                        ("employee_id", "=", data[0]),
                        ("date", "=", data[1]),
                        ("original", "not in", ["excess", "modified"]),
                    ]
                )
                if sheet:
                    sheet.update_attendance_sheet()
                else:
                    create_sheet = (
                        self.env["hr.attendance.sheet"]
                        .sudo()
                        .create({"employee_id": data[0], "date": data[1]})
                    )
                    create_sheet.update_attendance_sheet()

    def unlink(self):
        raise UserError(_("You're not allowed to delete me."))
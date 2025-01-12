# -*- coding: utf-8 -*-
# Native Python modules

# Local python modules

# Custom python modules

# Odoo modules
from odoo import models, fields, api, _
from odoo.tools.translate import _
from odoo.exceptions import UserError, ValidationError


class HrEmployeePrivate(models.Model):
    """
    NB: Any field only available on the model hr.employee (i.e. not on the
    hr.employee.public model) should have `groups="hr.group_hr_user"` on its
    definition to avoid being prefetched when the user hasn't access to the
    hr.employee model. Indeed, the prefetch loads the data for all the fields
    that are available according to the group defined on them.
    """

    _inherit = "hr.employee"

    @api.depends("age_today")
    def _compute_age(self):
        for user in self:
            if user.birthday:
                query = """SELECT age(now()::DATE, '%s'::DATE)::VARCHAR""" % (
                    self.birthday
                )
                self._cr.execute(query)
                value = self._cr.fetchone()
                if value:
                    user.age_today = value[0]
            else:
                user.age_today = False

    @api.depends("tenure_today")
    def _compute_tenure(self):
        for user in self:
            if user.date_hired:
                query = """SELECT age(now()::DATE, '%s'::DATE)::VARCHAR""" % (
                    self.date_hired
                )
                self._cr.execute(query)
                value = self._cr.fetchone()
                if value:
                    user.tenure_today = value[0]
            else:
                user.tenure_today = False

    employee_number = fields.Char(
        string="Employee ID Number", groups="hr.group_hr_user", tracking=True
    )

    # private partner
    lname = fields.Char(string="Last Name", groups="hr.group_hr_user", tracking=True)
    fname = fields.Char(string="First Name", groups="hr.group_hr_user", tracking=True)
    mname = fields.Char(string="Middle Name", groups="hr.group_hr_user", tracking=True)
    suffix = fields.Char(string="Suffix", groups="hr.group_hr_user", tracking=True)

    partner_id = fields.Many2one("res.partner", "Partner")

    # name updates onchange of lname,fname,mname,suffix
    @api.onchange("lname", "fname", "mname", "suffix")
    def _update_name(self):
        if self.lname == "":
            self.lname = False
        if self.fname == "":
            self.fname = False
        if self.mname == "":
            self.mname = False
        if self.suffix == "":
            self.suffix = False

        if self.lname is not False:
            if self.fname is not False:
                if self.mname is not False:
                    if self.suffix is not False:
                        self.name = (
                            self.lname
                            + ", "
                            + self.fname
                            + " "
                            + self.mname
                            + ", "
                            + self.suffix
                        )
                    elif self.suffix is False:
                        self.name = self.lname + ", " + self.fname + " " + self.mname
                elif self.mname is False:
                    if self.suffix is not False:
                        self.name = self.lname + ", " + self.fname + ", " + self.suffix
                    elif self.suffix is False:
                        self.name = self.lname + ", " + self.fname
            elif self.fname is False:
                if self.mname is not False:
                    if self.suffix is not False:
                        self.name = self.lname + ", " + self.mname + ", " + self.suffix
                    elif self.suffix is False:
                        self.name = self.lname + ", " + self.mname
                elif self.mname is False:
                    if self.suffix is not False:
                        self.name = self.lname + ", " + self.suffix
                    elif self.suffix is False:
                        self.name = self.lname
        elif self.lname is False:
            if self.fname is not False:
                if self.mname is not False:
                    if self.suffix is not False:
                        self.name = self.fname + " " + self.mname + ", " + self.suffix
                    elif self.suffix is False:
                        self.name = self.fname + " " + self.mname
                elif self.mname is False:
                    if self.suffix is not False:
                        self.name = self.fname + ", " + self.suffix
                    elif self.suffix is False:
                        self.name = self.fname
            elif self.fname is False:
                if self.mname is not False:
                    if self.suffix is not False:
                        self.name = self.mname + ", " + self.suffix
                    elif self.suffix is False:
                        self.name = self.mname
                elif self.mname is False:
                    if self.suffix is not False:
                        self.name = self.suffix
                    elif self.suffix is False:
                        self.name = False

    # Private Information
    age_today = fields.Char(
        string="Age Today", groups="hr.group_hr_user", compute="_compute_age"
    )

    # Goverment Informations
    sss_number = fields.Char("SSS Number", groups="hr.group_hr_user", tracking=True)
    philhealth_number = fields.Char(
        "Philhealth Number", groups="hr.group_hr_user", tracking=True
    )
    hdmf_id_number = fields.Char(
        "HDMF ID Number", groups="hr.group_hr_user", tracking=True
    )
    hmo_policy_number = fields.Char(
        "HMO Policy Number", groups="hr.group_hr_user", tracking=True
    )

    tin = fields.Char("TIN", groups="hr.group_hr_user", tracking=True)

    prc_license_number = fields.Char(
        "PRC License Number", groups="hr.group_hr_user", tracking=True
    )
    prc_date_issued = fields.Date(
        "PRC Date Issued", groups="hr.group_hr_user", tracking=True
    )
    prc_valid_until = fields.Date(
        "PRC Valid Until", groups="hr.group_hr_user", tracking=True
    )

    permanent_appointment = fields.Char(
        "Permanent Appointment", groups="hr.group_hr_user", tracking=True
    )
    bir_cert_no_of_dependents = fields.Char(
        "BIR Certified Number of Dependents", groups="hr.group_hr_user", tracking=True
    )

    # educational data tab
    employee_education_ids = fields.One2many(
        "hr.employee.education",
        "employee_id",
        string="Employee Education",
        groups="hr.group_hr_user",
        tracking=True,
    )
    employee_seminar_ids = fields.One2many(
        "hr.employee.seminar",
        "employee_id",
        string="Employee Seminar",
        groups="hr.group_hr_user",
        tracking=True,
    )

    # employement data tab
    date_hired = fields.Date(
        string="Date Hired", groups="hr.group_hr_user", tracking=True
    )
    tenure_today = fields.Char(
        string="Tenure Today",
        compute="_compute_tenure",
        groups="hr.group_hr_user",
        tracking=True,
    )

    notice_of_resignation = fields.Date(
        string="Notice of Resignation", groups="hr.group_hr_user", tracking=True
    )
    departure_date = fields.Date(
        string="Departure Date", groups="hr.group_hr_user", tracking=True
    )
    departure_reason = fields.Selection(
        [("fired", "Fired"), ("resigned", "Resigned"), ("retired", "Retired")],
        string="Departure Reason",
        groups="hr.group_hr_user",
        tracking=True,
    )
    departure_description = fields.Text(
        "Additional Information", groups="hr.group_hr_user", tracking=True
    )

    employee_position_ids = fields.One2many(
        "employee.position",
        "employee_id",
        string="Employee Position",
        groups="hr.group_hr_user",
        tracking=True,
    )

    # family data tab
    emergency_contact_relation = fields.Char(
        "Relationship to Employee", groups="hr.group_hr_user", tracking=True
    )

    maiden_name = fields.Char("Maiden Name", groups="hr.group_hr_user", tracking=True)
    spouse_name = fields.Char(
        string="Spouse Name", groups="hr.group_hr_user", tracking=True
    )
    spouse_occupation = fields.Char(
        string="Spouse Occupation", groups="hr.group_hr_user", tracking=True
    )
    spouse_employer = fields.Char(
        string="Spouse Employer", groups="hr.group_hr_user", tracking=True
    )
    spouse_work_location = fields.Char(
        string="Employer Location", groups="hr.group_hr_user", tracking=True
    )
    spouse_cell = fields.Char(
        string="Spouse Mobile", groups="hr.group_hr_user", tracking=True
    )
    spouse_tele = fields.Char(
        string="Spouse Phone", groups="hr.group_hr_user", tracking=True
    )
    marriage_date = fields.Date(
        string="Date of Marriage", groups="hr.group_hr_user", tracking=True
    )
    marriage_place = fields.Char(
        "Place of Marriage", groups="hr.group_hr_user", tracking=True
    )
    children = fields.Integer(
        string="Number of Children", groups="hr.group_hr_user", tracking=True
    )

    # FAMILY DATA / PARENTS
    mother_name = fields.Char(
        string="Mother's Name", groups="hr.group_hr_user", tracking=True
    )
    mother_citizenship = fields.Many2one(
        "res.country",
        string="Mother's Citizenship",
        groups="hr.group_hr_user",
        tracking=True,
    )
    mother_occupation = fields.Char(
        string="Mother's Occupation", groups="hr.group_hr_user", tracking=True
    )
    mother_address = fields.Text(
        string="Mother's Address", groups="hr.group_hr_user", tracking=True
    )

    father_name = fields.Char(
        string="Father's Name", groups="hr.group_hr_user", tracking=True
    )
    father_citizenship = fields.Many2one(
        "res.country",
        string="Father's Citizenship",
        groups="hr.group_hr_user",
        tracking=True,
    )
    father_occupation = fields.Char(
        string="Father's Occupation", groups="hr.group_hr_user", tracking=True
    )
    father_address = fields.Text(
        string="Father's Address", groups="hr.group_hr_user", tracking=True
    )

    employee_dependents_ids = fields.One2many(
        "employee.dependents",
        "employee_id",
        string="Employee Dependents",
        groups="hr.group_hr_user",
        tracking=True,
    )
    employee_relationship_ids = fields.One2many(
        "employee.relationship.line",
        "employee_id",
        string="Employee Relationship Line",
        groups="hr.group_hr_user",
        tracking=True,
    )

    employee_incident_ids = fields.One2many(
        "employee.incident",
        "employee_id",
        string="Employee Incident Report",
        groups="hr.group_hr_user",
        tracking=True,
    )

    job_description = fields.Text("Job Description")

    private_address = fields.Text("Address")
    bank_account = fields.Char("Bank Account Number")
    private_phone = fields.Char("Phone")
    email_private = fields.Char("Email")

    analytic_account_id = fields.Many2one(
        "account.analytic.account", "Analytic Account"
    )

    category_ids = fields.Many2many(groups="base.group_user")

    color = fields.Integer(groups="base.group_user")
    accounting_tag_id = fields.Many2one("hr.accounting.config")

    def write(self, vals):

        res = super(HrEmployeePrivate, self).write(vals)
        # if self.contract_id.state == 'open':
        if (
            self.contract_id.state == "open"
            and self.company_id.id != self.contract_id.company_id.id
        ):
            raise UserError(
                _("The company in the running contract record does not match.")
            )
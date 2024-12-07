# -*- coding: utf-8 -*-
# Native Python modules

# Local python modules

# Custom python modules
import httpx
from countryinfo import CountryInfo
from icecream import ic
import httpagentparser
from datetime import datetime, timezone as tzone
from zoneinfo import ZoneInfo

# Odoo modules
import odoo
from odoo import http
from odoo.addons.web.controllers.home import Home
from odoo.addons.web.controllers.utils import (
    ensure_db,
    _get_login_redirect_url,
    is_user_internal,
)
from odoo.http import request, route
from odoo.tools.translate import _

class IPHRAttendance(http.Controller):
    
    @http.route('/hr_attendance/systray_check_in_out', type="json", auth="user")
    def systray_attendance(self, latitude=False, longitude=False):
        result = super(IPHRAttendance, self).systray_attendance(latitude, longitude)
        
        # attendance log
        employee = request.env.user.employee_id
        user = request.env.user
        
        login_creds = request.env["ip.logger"].sudo().search(
            domain=[
                ("employee_id", "=", employee.id), 
                ("user_id", "=", user.id)
            ],
            order="login_date desc",
            limit=1,
        )
        
        return result
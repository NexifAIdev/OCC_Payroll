# -*- coding: utf-8 -*-
# Native Python modules

# Local python modules

# Custom python modules
import httpx
from countryinfo import CountryInfo
from icecream import ic

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

SIGN_UP_REQUEST_PARAMS = {
    "db",
    "login",
    "debug",
    "token",
    "message",
    "error",
    "scope",
    "mode",
    "redirect",
    "redirect_hostname",
    "email",
    "name",
    "partner_id",
    "password",
    "confirm_password",
    "city",
    "country_id",
    "lang",
    "signup_email",
}

class WebLoginIP(Home):
    def fetch_public_ip(self):
        """Fetch public IP address of the user using external API."""
        try:
            with httpx.Client() as client:
                response = client.get("https://api.ipify.org?format=json")
                response.raise_for_status()
                return response.json().get("ip")
        except httpx.HTTPStatusError:
            return None

    @http.route()
    def web_login(self, redirect=None, **kw):
        # Call the superclass method to keep Odoo's default behavior
        result = super().web_login(redirect=redirect, **kw)
        values = {k: v for k, v in request.params.items() if k in SIGN_UP_REQUEST_PARAMS}

        # Fetch IP address
        curr_ip_address = kw.get("user_ip")
        ic(curr_ip_address)
        ip_address_db = request.env["res.ip.address"].sudo()

        # Custom IP restriction and bypass logic
        if request.httprequest.method == "POST":
            old_uid = request.uid

            if request.params.get("login"):
                user_rec = (
                    request.env["res.users"]
                    .sudo()
                    .search([("login", "=", request.params["login"])])
                )

                # Check if user has group permissions to bypass IP restriction
                bypass_ip_check = [
                    user_rec.has_group("base.group_system"),
                    user_rec.has_group("occ_configurations.group_ls_admin"),
                    user_rec.has_group("occ_configurations.group_wfh_employee"),
                ]
                ic(any(bypass_ip_check))

                if any(bypass_ip_check):
                    # Bypass IP check for permitted groups
                    try:
                        uid = request.session.authenticate(
                            request.session.db,
                            request.params["login"],
                            request.params["password"],
                        )
                        request.params["login_success"] = True
                        return request.redirect(self._login_redirect(uid, redirect=redirect))
                    except odoo.exceptions.AccessDenied:
                        request.update_env = old_uid
                        values["error"] = _("Wrong login/password")
                else:
                    # Enforce IP restriction
                    if curr_ip_address:
                        allowed_ip = ip_address_db.search(
                            [("ip_address", "=", curr_ip_address)], limit=1
                        )
                        ic(allowed_ip)
                        if allowed_ip:
                            # User IP is allowed
                            try:
                                uid = request.session.authenticate(
                                    request.session.db,
                                    request.params["login"],
                                    request.params["password"],
                                )
                                request.params["login_success"] = True
                                return request.redirect(self._login_redirect(uid, redirect=redirect))
                            except odoo.exceptions.AccessDenied:
                                request.update_env = old_uid
                                values["error"] = _("You cannot sign with your current IP address")
                        else:
                            # IP is not in the allowed list
                            request.update_env = old_uid
                            values["error"] = _("Not allowed to login from this IP")
                    else:
                        ic("Enforce IP restrictions")
                        request.update_env = old_uid
                        values["error"] = _("You cannot sign with your current IP address")

        # Update values for the login page rendering
        if "login" not in values and request.session.get("auth_login"):
            values["login"] = request.session.get("auth_login")
        if not odoo.tools.config["list_db"]:
            values["disable_database_manager"] = True
            
        ic(values)
        if values.get("error"):
            raise odoo.exceptions.AccessDenied(values["error"])

        response = request.render("web.login", values)
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["Content-Security-Policy"] = "frame-ancestors 'self'"
        return response
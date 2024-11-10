# -*- coding: utf-8 -*-
# Native Python modules

# Local python modules

# Custom python modules
import httpx
from countryinfo import CountryInfo
from icecream import ic
import httpagentparser

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
            with httpx.Client(timeout=10) as client:
                response = client.get("https://api.ipify.org?format=json")
                response.raise_for_status()
                return response.json().get("ip")
        except httpx.HTTPStatusError:
            return None

    @http.route(website=True, type="http", auth="public", sitemap=False)
    def web_login(self, redirect=None, **kw):
        ensure_db()

        # Initialize values and params
        values = {k: v for k, v in request.params.items() if k in ["login", "password"]}
        request.params["login_success"] = False
        values["error"] = None

        if request.httprequest.method == "GET" and redirect and request.session.uid:
            return request.redirect(redirect)

        # Handle user environment setup
        if request.env.uid is None:
            if request.session.uid is None:
                request.env["ir.http"]._auth_method_public()
            else:
                request.update_env(user=request.session.uid)

        # Check if this is a POST request (login attempt)
        if request.httprequest.method == "POST" and request.params.get("login"):
            # Fetch IP address and user agent before authentication
            curr_ip_address = (
                kw.get("user_ip")
                or request.params.get("user_ip")
                or request.httprequest.environ.get("HTTP_X_FORWARDED_FOR")
                or request.httprequest.environ.get("REMOTE_ADDR")
            )
            ip_address_db = request.env["res.ip.address"].sudo()

            # Get user record to check groups
            user_rec = (
                request.env["res.users"]
                .sudo()
                .search([("login", "=", request.params["login"])], limit=1)
            )

            # Check bypass conditions
            bypass_ip_check = [
                user_rec.id == 2,  # Admin user
                user_rec.has_group("occ_configurations.group_ls_admin"),
                user_rec.has_group("occ_configurations.group_wfh_employee"),
            ]

            # Validate IP if necessary
            if not any(bypass_ip_check) and curr_ip_address:
                allowed_ip = ip_address_db.search(
                    [("ip_address", "=", curr_ip_address)], limit=1
                )
                if not allowed_ip:
                    values["error"] = _("You cannot sign in from this IP address")
                    response = request.render("web.login", values)
                    response.headers["X-Frame-Options"] = "SAMEORIGIN"
                    response.headers["Content-Security-Policy"] = (
                        "frame-ancestors 'self'"
                    )
                    return response

            # Only proceed with authentication if IP check passed
            if not values["error"]:
                try:
                    uid = request.session.authenticate(
                        request.session.db,
                        request.params["login"],
                        request.params["password"],
                    )
                    request.params["login_success"] = True

                    # Collect browser info after successful login
                    agent_details = httpagentparser.detect(
                        request.httprequest.environ.get("HTTP_USER_AGENT")
                    )
                    user_os = agent_details.get("os", {}).get("name", "Unknown")
                    browser_name = agent_details.get("browser", {}).get(
                        "name", "Unknown"
                    )

                    return request.redirect(
                        self._login_redirect(uid, redirect=redirect)
                    )
                except odoo.exceptions.AccessDenied:
                    values["error"] = _("Wrong login/password")

        # Handle the non-POST cases (initial page load, etc.)
        if "login" not in values and request.session.get("auth_login"):
            values["login"] = request.session.get("auth_login")

        if not odoo.tools.config["list_db"]:
            values["disable_database_manager"] = True

        response = request.render("web.login", values)
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["Content-Security-Policy"] = "frame-ancestors 'self'"

        return response

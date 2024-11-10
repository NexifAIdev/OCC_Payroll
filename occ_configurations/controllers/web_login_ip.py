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

    @http.route(website=True, type="http", auth="public", sitemap=False)
    def web_login(self, redirect=None, **kw):
        ensure_db()
        result = super(WebLoginIP, self).web_login(redirect=redirect, **kw)
        request.params["login_success"] = False
        if request.httprequest.method == "GET" and redirect and request.session.uid:
            return request.redirect(redirect)
        if request.env.uid is None:
            if request.session.uid is None:
                request.env["ir.http"]._auth_method_public()
            else:
                request.update_env(user=request.session.uid)

        values = {k: v for k, v in request.params.items() if k in ["login", "password"]}
        # ic(request.httprequest.environ)

        try:
            values["databases"] = http.db_list()
        except odoo.exceptions.AccessDenied:
            values["databases"] = None

        curr_ip_address = (
            kw.get("user_ip")
            or request.params.get("user_ip")
            or request.httprequest.environ["REMOTE_ADDR"]
        )

        curr_user_agent = request.httprequest.environ["HTTP_USER_AGENT"]

        ip_address_db = request.env["res.ip.address"].sudo()
        values["error"] = None

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
                if not any(bypass_ip_check):
                    # Enforce IP restriction
                    ic(curr_ip_address)
                    if curr_ip_address:
                        allowed_ip = ip_address_db.search(
                            [("ip_address", "=", curr_ip_address)], limit=1
                        )
                        ic(allowed_ip)
                        if not allowed_ip:
                            # IP is not in the allowed list
                            values["error"] = _(
                                "You cannot sign in from this IP address"
                            )
                            request.update_env = old_uid
                    else:
                        values["error"] = _("You cannot sign in from this IP address")
                        request.update_env = old_uid

                ic(values["error"])
                # Only allow authentication if no error
                if not values["error"]:
                    try:
                        uid = request.session.authenticate(
                            request.session.db,
                            request.params["login"],
                            request.params["password"],
                        )
                        request.params["login_success"] = True
                        return request.redirect(
                            self._login_redirect(uid, redirect=redirect)
                        )
                    except odoo.exceptions.AccessDenied:
                        request.update_env = old_uid
                        values["error"] = _("Wrong login/password")

        # Render login page with error if any
        # if values.get("error"):
        if "login" not in values and request.session.get("auth_login"):
            values["login"] = request.session.get("auth_login")
        if not odoo.tools.config["list_db"]:
            values["disable_database_manager"] = True
        response = request.render("web.login", values)
        ic(values)
        ic(response)
        ic(request.params)
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["Content-Security-Policy"] = "frame-ancestors 'self'"
        return response

        # return result

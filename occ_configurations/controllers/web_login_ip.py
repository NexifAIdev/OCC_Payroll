# -*- coding: utf-8 -*-
# Native Python modules

# Local python modules

# Custom python modules
import httpx

# Odoo modules
import odoo
from odoo import http
from odoo.addons.web.controllers import home
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


class WebLoginIP(home.Home):
    
    def fetch_public_ip(self):
        client_ip = (
            request.httprequest.headers.get("X-Forwarded-For") or  # Check if the IP is forwarded by a proxy
            request.httprequest.headers.get("X-Real-IP") or  # Check if a reverse proxy set this IP
            request.httprequest.environ.get("REMOTE_ADDR")  # Default to REMOTE_ADDR if no headers are present
        )
        
        print(request.httprequest.headers.get("X-Forwarded-For"))
        print(request.httprequest.headers.get("X-Real-IP"))
        print(f"Client IP address: {client_ip}")
        try:
            with httpx.Client() as client:
                response = client.get("https://httpbin.org/ip")
                httpbin_ip = response.json().get("origin")
                print(f"{httpbin_ip=}")
            
            with httpx.Client() as client:
                response = client.get("https://api.ipify.org?format=json")
                response.raise_for_status()  # Raise an error for non-2xx responses
                ip_data = response.json()
                print(ip_data)
                return ip_data.get("ip")
        except httpx.HTTPStatusError as e:
            print(f"Failed to get public IP from ipify: {e}")
            return None

    def fetch_geolocation(self, ip_address):
        try:
            with httpx.Client() as client:
                response = client.get(f"https://ipapi.co/{ip_address}/json/")
                response.raise_for_status()
                location_data = response.json()
                return location_data
        except httpx.HTTPStatusError as e:
            print(f"Failed to get geolocation for IP {ip_address}: {e}")
            return None

    def get_location(self, ip_address):
        response = request.get(
            f"http://ip-api.com/json/{ip_address}", timeout=20
        ).json()

        return {"country": response.get("country")}

    @route("/web/login", type="http", auth="none")
    def web_login(self, redirect=None, **kw):
        print(f"{kw=}")
        ensure_db()
        request.params["login_success"] = False
        ip_address_db = request.env["res.ip.address"]
        print(f"""{request.params.get("user_ip")=}""")
        curr_ip_address = request.params.get("user_ip") or self.fetch_public_ip()
        print(f"----------------------{curr_ip_address=}")

        if request.httprequest.method == "GET" and redirect and request.session.uid:
            print(f"{request.httprequest.method=}, {redirect=}, {request.session.uid=}")
            return request.redirect(redirect)

        if request.env.uid is None:
            if request.session.uid is None:
                request.env["ir.http"]._auth_method_public()
            else:
                request.update_env(user=request.session.uid)

        values = {
            k: v for k, v in request.params.items() if k in SIGN_UP_REQUEST_PARAMS
        }
        
        print(f"{values=}")

        try:
            values["databases"] = http.db_list()
        except odoo.exceptions.AccessDenied:
            values["databases"] = None

        print(f"{values=}")
        if request.httprequest.method == "POST":
            old_uid = request.uid
            print(f"{old_uid=}")
            if request.params["login"]:
                user_rec = (
                    request.env["res.users"]
                    .sudo()
                    .search([("login", "=", request.params["login"])])
                )
                print(f"{user_rec=}")

                bypass_ip_check = [
                    user_rec.has_group("occ_configurations.group_ls_admin"),
                    user_rec.has_group("occ_configurations.group_wfh_employee"),
                ]
                
                print(f"{any(bypass_ip_check)=}")

                if any(bypass_ip_check):
                    # User belongs to one of the bypass groups; skip IP checking
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
                    except odoo.exceptions.AccessDenied as e:
                        request.update_env = old_uid
                        if e.args == odoo.exceptions.AccessDenied().args:
                            values["error"] = _("Wrong login/password")
                else:
                    # Check if user has allowed IPs
                    if curr_ip_address:
                        print(f"{curr_ip_address=}")
                        allowed_ip = ip_address_db.search(
                            domain=[("ip_address", "=", curr_ip_address)],
                            limit=1,
                        )
                        print(f"{allowed_ip=}")
                        if allowed_ip:
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
                            except odoo.exceptions.AccessDenied as e:
                                request.update_env = old_uid
                                if e.args == odoo.exceptions.AccessDenied().args:
                                    values["error"] = _("Wrong login/password")
                        else:
                            request.update_env = old_uid
                            values["error"] = _("Not allowed to login from this IP")
                    else:
                        # No IP restriction for this user, proceed with login
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
                        except odoo.exceptions.AccessDenied as e:
                            request.update_env = old_uid
                            if e.args == odoo.exceptions.AccessDenied().args:
                                values["error"] = _("Wrong login/password")
        else:
            if "error" in request.params and request.params.get("error") == "access":
                values["error"] = _("Please contact the administrator.")

        if "login" not in values and request.session.get("auth_login"):
            values["login"] = request.session.get("auth_login")
        if not odoo.tools.config["list_db"]:
            values["disable_database_manager"] = True
        response = request.render("web.login", values)
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["Content-Security-Policy"] = "frame-ancestors 'self'"
        return response

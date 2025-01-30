# -*- coding: utf-8 -*-
# Native Python modules

# Local python modules

# Custom python modules
import httpx
from countryinfo import CountryInfo
from icecream import ic
import httpagentparser
from user_agents import parse
from datetime import datetime, timezone as tzone
from zoneinfo import ZoneInfo

ic.disable()

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
    
    def fetch_public_ip_info(self, ip=None):
        """Fetch public IP address and additional location info for a given IP using various external APIs."""
        # Define API endpoints and field mappings
        api_endpoints = [
            {
                "url": f"https://apip.cc/api-json/{ip}" if ip else "https://apip.cc/api-json/",
                "fields": {
                    "ip": "IP",
                    "country": "CountryName",
                    "region": "RegionName",
                    "city": "City",
                    "latitude": "Latitude",
                    "longitude": "Longitude",
                    "timezone": "TimeZone",
                    "postal": "Postal",
                    "currency": "Currency",
                },
                "supports_ip_query": True,
            },
            {
                "url": f"https://api.techniknews.net/ipgeo/{ip}" if ip else "https://api.techniknews.net/ipgeo/",
                "fields": {
                    "ip": "query",
                    "country": "country",
                    "region": "regionName",
                    "city": "city",
                    "latitude": "lat",
                    "longitude": "lon",
                    "timezone": "timezone",
                    "postal": "zip",
                    "currency": "currency",
                },
                "supports_ip_query": True,
            },
        ]
        
        # Iterate over APIs to retrieve data
        for api in api_endpoints:
            try:
                # Construct URL based on whether the API supports IP-based queries
                url = api["url"]
                with httpx.Client(timeout=10) as client:
                    response = client.get(url, follow_redirects=True)
                    response.raise_for_status()
                    data = response.json()
                    ip_info = {key: data.get(field) for key, field in api["fields"].items()}
                
                    if ip_info.get("ip"):
                        break

            except httpx.RequestError as e:
                ic(f"Request to {api['url']} failed: {e}")
            except httpx.HTTPStatusError as e:
                ic(f"HTTP error from {api['url']}: {e}")
            except Exception as e:
                ic(f"Unexpected error from {api['url']}: {e}")

        return ip_info

    @http.route(website=True, type="http", auth="public", sitemap=False)
    def web_login(self, redirect=None, **kw):
        ensure_db()
        
        # ic(f"{kw=}")
        # ic(f"{request.params=}")

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
            # ic(request.geoip.city.name)
            # ic(request.geoip.country.name)
            # ic(request.geoip.continent.name)
            # ic(request.geoip.location.latitude)
            # ic(request.geoip.location.longitude)
            # ic(request.geoip.ip)
            # ic(request.httprequest.user_agent.browser)
            # ic(request.httprequest.user_agent)
            curr_ip_address = (
                kw.get("user_ip")
                or request.params.get("user_ip")
                or request.httprequest.environ.get("HTTP_X_FORWARDED_FOR")
                or request.httprequest.environ.get("REMOTE_ADDR")
            )
            ip_info = self.fetch_public_ip_info(curr_ip_address)
            ip_address_db = request.env["res.ip.address"].sudo()
            # Collect Login Info
            useragent_string = request.httprequest.environ.get("HTTP_USER_AGENT")
            agent_details = httpagentparser.detect(useragent_string)
            user_agent = parse(useragent_string)
            
            device_type = user_agent.device.family
            if user_agent.is_mobile:
                device_type = "Phone"
            elif user_agent.is_tablet:
                device_type = "Tablet"
            elif user_agent.is_pc:
                device_type = "Desktop"
            else:
                device_type = "Unknown"
            
            user_os = user_agent.os.family or agent_details.get("os", {}).get("name", "Unknown")
            browser_name = user_agent.browser.family or agent_details.get("browser", {}).get(
                "name", "Unknown"
            )
            device_name = device_type or agent_details.get("platform", {}).get(
                "name", "Unknown"
            )
            lat = (
                kw.get("lat") 
                or request.params.get("lat") 
                or (
                    ip_info["latitude"] 
                    if ip_info.get("latitude") 
                    else 0.0
                )
            )
            lon = (
                kw.get("lon") 
                or request.params.get("lon") 
                or (
                    ip_info["longitude"] 
                    if ip_info.get("longitude") 
                    else 0.0
                )
            )
            
            lat = float(lat) if lat else 0.0
            lon = float(lon) if lon else 0.0
            
            country = ip_info["country"] if ip_info.get("country") else "Unknown"
            region = ip_info["region"] if ip_info.get("region") else "Unknown"
            city = ip_info["city"] if ip_info.get("city") else "Unknown"
            postal = ip_info["postal"] if ip_info.get("postal") else "Unknown"
            currency = ip_info["currency"] if ip_info.get("currency") else "USD"
            timezone = ip_info["timezone"] if ip_info.get("timezone") else "Europe/Brussels"
            
            
            # Get user record to check groups
            user_rec = (
                request.env["res.users"]
                .sudo()
                .search([("login", "=", request.params["login"])], limit=1)
            )

            # Check bypass conditions
            bypass_ip_check = [
                # Admin user
                user_rec.id == 2,
                # OCC Devs
                user_rec.has_group("occ_configurations.group_occ_core_developers"),
                # IP Admins
                user_rec.has_group("occ_configurations.group_ls_admin"),
                user_rec.has_group("occ_configurations.group_ip_address_configuration"),
                # Normal Employees (WFH)
                user_rec.has_group("occ_configurations.group_wfh_employee"),
            ]
            
            block_access_platforms = [
                user_agent.is_mobile,
                user_agent.is_tablet,
                user_agent.is_bot,
            ]
            
            ip_logger_user = request.env["ip.logger"]
            user_time = datetime.now()
            # user_time = current_time_utc.astimezone(ZoneInfo(timezone))
            
            name_fields = [
                curr_ip_address,
                browser_name,
                user_os,
            ]
            
            location_fields = [
                country,
                region,
                city,
            ]
            
            ip_logger_user.sudo().create(
                {
                    "name": " | ".join([f for f in name_fields if f]),
                    "user_agent": request.httprequest.environ.get("HTTP_USER_AGENT"),
                    "ip_address": curr_ip_address,
                    "browser_name": browser_name,
                    "os_name": user_os,
                    "device_name": device_name,
                    "lattitude": lat,
                    "longitude": lon,
                    "location_name": " | ".join([f for f in location_fields if f]),
                    "country": country,
                    "region": region,
                    "city": city,
                    "zip_code": postal,
                    "currency": currency,
                    "timezone": timezone,
                    "user_id": user_rec.id if user_rec else False,
                    "employee_id": user_rec.employee_id.id if user_rec else False,
                    "login_date": user_time,
                }
            )
            

            # Validate IP if necessary
            if not any(bypass_ip_check) and curr_ip_address and not any(block_access_platforms):
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

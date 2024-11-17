/** @odoo-module **/
import publicWidget from '@web/legacy/js/public/public_widget';

console.log("IP Logger is running");

publicWidget.registry.userIpAddress = publicWidget.Widget.extend({
    selector: '.oe_login_buttons .btn-primary',  // Target the login button specifically

    events: {
        'click': '_onLoginButtonClick',  // Trigger IP fetch when the login button is clicked
    },

    async _onLoginButtonClick(event) {
        event.preventDefault();

        const urls = [
            "https://api.ipify.org?format=json",
            "https://httpbin.org/ip",
            "https://ipv4.getmyip.dev/",
            "https://api.iplocation.net/?cmd=get-ip",
            "https://apip.cc/json",
            "https://api.ipapi.is",
            "https://api.techniknews.net/ipgeo",
            "https://ipinfo.io/json",
            "https://api.aruljohn.com/ip/json",
        ];

        let ip = null;

        for (const url of urls) {
            try {
                const response = await fetch(url);
                const data = await response.json();

                if (data.ip) {
                    ip = data.ip;
                } else if (data.ipv4) {
                    ip = data.ipv4;
                } else if (data.query) {
                    ip = data.query;
                } else if (data.address) {
                    ip = data.address;
                } else if (data.clientIP) {
                    ip = data.clientIP;
                } else if (data.IPv4) {
                    ip = data.IPv4;
                }

                if (ip) break;
            } catch (error) {
                console.warn(`Failed to fetch IP from ${url}:`, error);
                continue;
            }
        }

        if (ip) {
            let ipInput = document.getElementById("user_ip");
            if (!ipInput) {
                // Create the hidden input if it doesn't exist
                ipInput = document.createElement("input");
                ipInput.type = "hidden";
                ipInput.name = "user_ip";
                ipInput.id = "user_ip";
                ipInput.style.display = "none";
                this.el.closest('form').appendChild(ipInput);
            }
            ipInput.value = ip;
            // console.log("User IP set in hidden input:", ip);
        } else {
            console.error("Failed to fetch IP address from all APIs.");
        }

        let latitudeInput = document.getElementById("user_lat");
        let longitudeInput = document.getElementById("user_long");
        if (!latitudeInput) {
            latitudeInput = document.createElement("input");
            latitudeInput.name = "user_lat";
            latitudeInput.id = "user_lat";
            latitudeInput.style.display = "none";
            this.el.closest('form').appendChild(latitudeInput);
        }

        if (!longitudeInput) {
            longitudeInput = document.createElement("input");
            longitudeInput.name = "user_long";
            longitudeInput.id = "user_long";
            longitudeInput.style.display = "none";
            this.el.closest('form').appendChild(longitudeInput);
        }

        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(function(position) {
                latitudeInput.value = position.coords.latitude;
                longitudeInput.value = position.coords.longitude;
            });
        }
        else {
            console.warn("Geolocation is not supported or blocked by this browser or .");
            latitudeInput.value = 0;
            longitudeInput.value = 0;
        }

        this.el.closest('form').submit();
    },
});

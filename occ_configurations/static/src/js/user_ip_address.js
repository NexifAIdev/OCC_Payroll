/** @odoo-module **/
import publicWidget from '@web/legacy/js/public/public_widget';

// Public widget for setting the IP address in the 'user_ip' input field
publicWidget.registry.userIpAddress = publicWidget.Widget.extend({
    selector: '.oe_login_buttons .btn-primary',  // Target the login button specifically

    events: {
        'click': '_onLoginButtonClick',  // Trigger IP fetch when the login button is clicked
    },

    async _onLoginButtonClick(event) {
        // Prevent form submission until IP address is fetched
        event.preventDefault();

        // List of API URLs to try
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

        // Try each URL until a valid IP is retrieved
        for (const url of urls) {
            try {
                const response = await fetch(url);
                const data = await response.json();

                // Extract the IP from each API's specific response structure
                if (data.ip) {           // For api.ipify.org, httpbin.org, ipinfo.io
                    ip = data.ip;
                } else if (data.ipv4) {  // For ipv4.getmyip.dev
                    ip = data.ipv4;
                } else if (data.query) { // For api.iplocation.net
                    ip = data.query;
                } else if (data.address) { // For apip.cc
                    ip = data.address;
                } else if (data.clientIP) { // For api.techniknews.net/ipgeo
                    ip = data.clientIP;
                } else if (data.IPv4) { // For api.ipapi.is
                    ip = data.IPv4;
                } else if (data.address) { // For api.aruljohn.com
                    ip = data.address;
                }

                // If we got an IP, stop iterating through the URLs
                if (ip) break;
            } catch (error) {
                console.warn(`Failed to fetch IP from ${url}:`, error);
                continue; // Proceed to the next API if this one fails
            }
        }

        if (ip) {
            // Set the value of the existing hidden 'user_ip' input
            const ipInput = document.getElementById("user_ip");
            if (ipInput) {
                ipInput.value = ip;
                console.log("User IP set in hidden input:", ip);
            }
        } else {
            console.error("Failed to fetch IP address from all APIs.");
        }

        // After setting the IP (or if unsuccessful), submit the form
        this.el.closest('form').submit();
    },
});

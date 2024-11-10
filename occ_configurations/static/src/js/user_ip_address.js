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

        try {
            // Fetch the user's public IP address
            const response = await fetch("https://api.ipify.org?format=json");
            const data = await response.json();

            // Set the value of the existing hidden 'user_ip' input
            const ipInput = document.getElementById("user_ip");
            if (ipInput) {
                ipInput.value = data.ip;
                console.log("User IP set in hidden input:", data.ip);
            }

            // After setting the IP, submit the form
            this.el.closest('form').submit();

        } catch (error) {
            console.error("Failed to fetch IP address:", error);
            // Optionally submit the form even if IP fetch fails
            this.el.closest('form').submit();
        }
    },
});

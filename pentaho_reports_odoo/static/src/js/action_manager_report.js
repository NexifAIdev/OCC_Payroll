odoo.define('web_report_type_pentaho_willdoo.qwebactionmanager', function( require ){
"use strict";

    var core = require("web.core");
    var ActionManager = require("web.ActionManager");
    var framework = require("web.framework");
    var session = require("web.session");
    var _t = core._t;

    ActionManager.include({

        _executeReportAction: function (action, options) {
            if (action.report_type === 'pentaho') {
                return this._triggerDownload(action, options, 'pentaho');
            }
            return this._super.apply(this, arguments);
        },

        _makeReportUrls: function (action) {
            var reportUrls = this._super.apply(this, arguments);
            reportUrls.pentaho = reportUrls['html'].replace('html', 'pentaho');
            return reportUrls;
        },

        _downloadReport: function (url) {
            if (url.split('/')[2] === 'pentaho') {
                return this._downloadPenathoReport(url);
            };
            return this._super.apply(this, arguments);
        },

        _downloadPenathoReport: function (url) {
            var self = this;

            framework.blockUI();
            return new Promise(function (resolve, reject) {
                var type = "pdf";
                var blocked = !session.get_file({
                    url: url,
                    data: {
                        data: JSON.stringify([url, type]),
                        context: JSON.stringify(session.user_context),
                    },
                    success: resolve,
                    error: (error) => {
                        self.call('crash_manager', 'rpc_error', error);
                        reject();
                    },
                    complete: framework.unblockUI,
                });
                if (blocked) {
                    // AAB: this check should be done in get_file service directly,
                    // should not be the concern of the caller (and that way, get_file
                    // could return a deferred)
                    var message = _t('A popup window with your report was blocked. You ' +
                                     'may need to change your browser settings to allow ' +
                                     'popup windows for this page.');
                    this.do_warn(_t('Warning'), message, true);
                }
            })
        },

    });
});

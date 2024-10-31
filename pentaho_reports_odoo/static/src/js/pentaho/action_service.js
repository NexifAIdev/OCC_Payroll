/** @odoo-module **/

import {download} from "@web/core/network/download";
import {registry} from "@web/core/registry";

async function render_report(action, options, env) {
    // console.log("render_report");
    // console.log(action);
    if (action.report_type === "pentaho") {

        const type = action.report_type;
        let url = `/report/${type}/${action.report_name}`;
        const actionContext = action.context || {};
        if (action.data && JSON.stringify(action.data) !== "{}") {
            // Build a query string with `action.data` (it's the place where reports
            // using a wizard to customize the output traditionally put their options)
            const action_options = encodeURIComponent(JSON.stringify(action.data));
            const context = encodeURIComponent(JSON.stringify(actionContext));
            url += `?options=${action_options}&context=${context}`;
        } else {
            if (actionContext.active_ids) {
                url += `/${actionContext.active_ids.join(",")}`;
            }
            if (type === "pentaho") {
                const context = encodeURIComponent(
                    JSON.stringify(env.services.user.context)
                );
                url += `?context=${context}`;
            }
        }
        
        env.services.ui.block();
        try {

            const orm = env.services.orm;
            let datas = await orm.call("ir.actions.report", "render_report", [{}], {context: {'a':action}});
            // console.log(datas);

            await download({
                url: "/pentaho/download",
                data: {
                    data: JSON.stringify(datas),
                    context: JSON.stringify(env.services.user.context),
                },
            });

            // console.log(datas,[url, action.report_type],env.services.user.context)
        } finally {
            env.services.ui.unblock();
        }
        const onClose = options.onClose;
        if (action.close_on_report_download) {
            return env.services.action.doAction(
                {type: "ir.actions.act_window_close"},
                {onClose}
            );
        } else if (onClose) {
            onClose();
        }
        return Promise.resolve(true);
    }
    return Promise.resolve(false);

}

registry.category("ir.actions.report handlers").add("pentaho_handler",render_report);

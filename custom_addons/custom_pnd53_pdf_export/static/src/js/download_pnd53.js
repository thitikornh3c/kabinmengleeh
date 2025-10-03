/** @odoo-module **/

import { registry } from "@web/core/registry";

registry.category("actions").add("download_pnd53_pdf", function (env, action) {
    const { links } = action.params;
    if (links && links.length) {
        links.forEach(link => {
            const a = document.createElement("a");
            a.href = link;
            a.download = "";
            a.target = "_blank";
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
        });
    }
    return Promise.resolve();
});

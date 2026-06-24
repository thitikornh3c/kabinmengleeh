/** @odoo-module **/

import { ActionpadWidget } from "@point_of_sale/app/screens/product_screen/action_pad/action_pad";
import { patch } from "@web/core/utils/patch";
import { TwoBookButton } from "./two_book_button";

patch(ActionpadWidget, {
    components: { ...ActionpadWidget.components, TwoBookButton },
});

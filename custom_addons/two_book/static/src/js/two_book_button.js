/** @odoo-module **/

import { Component } from "@odoo/owl";
import { usePos } from "@point_of_sale/app/hooks/pos_hook";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";
import { applyTwoBookFiscalPosition } from "./two_book_pos_order";

export class TwoBookButton extends Component {
    static template = "two_book.TwoBookButton";
    static props = {};

    setup() {
        this.pos = usePos();
        this.notification = useService("notification");
    }

    get twoBookEnabled() {
        const config = this.pos.config;
        return Boolean(config.enable_two_book ?? config.raw?.enable_two_book);
    }

    get currentOrder() {
        return this.pos.getOrder();
    }

    get isVatOrder() {
        return Boolean(this.currentOrder?.is_vat_order);
    }

    get buttonLabel() {
        return this.isVatOrder
            ? _t("ใบกำกับภาษี (VAT)")
            : _t("บิลเงินสด (Non-VAT)");
    }

    get buttonClass() {
        const base =
            "two-book-btn btn btn-lg py-3 d-flex align-items-center justify-content-center flex-fill text-truncate";
        return this.isVatOrder ? `${base} btn-success vat-active` : `${base} btn-secondary non-vat-active`;
    }

    toggleVatMode() {
        const order = this.currentOrder;
        if (!order) {
            return;
        }

        const newValue = !order.is_vat_order;
        order.is_vat_order = newValue;
        applyTwoBookFiscalPosition(order, newValue);

        this.notification.add(
            newValue
                ? _t("เปลี่ยนเป็น: ออกใบกำกับภาษี (VAT 7%)")
                : _t("เปลี่ยนเป็น: บิลเงินสด (ไม่ออกใบกำกับ)"),
            { type: newValue ? "success" : "warning" }
        );
    }
}

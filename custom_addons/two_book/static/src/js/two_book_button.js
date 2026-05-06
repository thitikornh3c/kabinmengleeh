/** @odoo-module **/

import { Component } from "@odoo/owl";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";

/**
 * TwoBookButton - ปุ่มสลับ VAT / Non-VAT ใน POS
 * แสดงใน ActionpadWidget (ด้านขวาของหน้าจอ POS)
 */
export class TwoBookButton extends Component {
    static template = "two_book.TwoBookButton";
    static props = {};

    setup() {
        this.pos = usePos();
        this.notification = useService("notification");
    }

    get currentOrder() {
        return this.pos.get_order();
    }

    get isVatOrder() {
        return this.currentOrder?.is_vat_order ?? false;
    }

    get buttonLabel() {
        return this.isVatOrder
            ? _t("ใบกำกับภาษี (VAT)")
            : _t("บิลเงินสด (Non-VAT)");
    }

    get buttonClass() {
        return this.isVatOrder
            ? "two-book-btn vat-active"
            : "two-book-btn non-vat-active";
    }

    toggleVatMode() {
        const order = this.currentOrder;
        if (!order) return;

        const newValue = !order.is_vat_order;
        order.is_vat_order = newValue;

        // อัปเดต Fiscal Position ตามการเลือก
        this._applyFiscalPosition(order, newValue);

        this.notification.add(
            newValue
                ? _t("เปลี่ยนเป็น: ออกใบกำกับภาษี (VAT 7%)")
                : _t("เปลี่ยนเป็น: บิลเงินสด (ไม่ออกใบกำกับ)"),
            { type: newValue ? "success" : "warning", duration: 2000 }
        );
    }

    _applyFiscalPosition(order, isVat) {
        const config = this.pos.config;
        if (!config.enable_two_book) return;

        if (isVat && config.two_book_vat_fiscal_position_id) {
            const fp = this.pos.models["account.fiscal.position"].find(
                (f) => f.id === config.two_book_vat_fiscal_position_id[0]
            );
            order.fiscal_position = fp || null;
        } else if (!isVat && config.two_book_non_vat_fiscal_position_id) {
            const fp = this.pos.models["account.fiscal.position"].find(
                (f) => f.id === config.two_book_non_vat_fiscal_position_id[0]
            );
            order.fiscal_position = fp || null;
        }

        // Recompute taxes บน order lines ทั้งหมด
        for (const line of order.get_orderlines()) {
            line.set_quantity(line.get_quantity());
        }
    }
}

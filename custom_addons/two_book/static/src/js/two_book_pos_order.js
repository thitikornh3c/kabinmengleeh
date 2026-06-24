/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { PosOrder } from "@point_of_sale/app/models/pos_order";
import { PosStore } from "@point_of_sale/app/services/pos_store";

function isTwoBookEnabled(config) {
    return Boolean(config?.enable_two_book ?? config?.raw?.enable_two_book);
}

function getConfigRelationId(config, fieldName) {
    const value = config[fieldName] ?? config.raw?.[fieldName];
    return value?.id ?? value;
}

function applyTwoBookFiscalPosition(order, isVat) {
    const config = order.config;
    if (!isTwoBookEnabled(config)) {
        return;
    }
    const fpId = isVat
        ? getConfigRelationId(config, "two_book_vat_fiscal_position_id")
        : getConfigRelationId(config, "two_book_non_vat_fiscal_position_id");
    if (!fpId) {
        return;
    }
    const fp = order.models["account.fiscal.position"].get(fpId);
    order.fiscal_position_id = fp || order.fiscal_position_id;
    order.triggerRecomputeAllPrices();
}

patch(PosOrder.prototype, {
    setup(vals) {
        super.setup(...arguments);
        if (vals.is_vat_order !== undefined) {
            this.is_vat_order = vals.is_vat_order;
        } else if (this.is_vat_order === undefined) {
            this.is_vat_order = false;
        }
    },

    serializeForORM(opts = {}) {
        const data = super.serializeForORM(opts);
        data.is_vat_order = Boolean(this.is_vat_order);
        return data;
    },
});

patch(PosStore.prototype, {
    createNewOrder(data = {}) {
        const config = this.config;
        const isVatDefault = isTwoBookEnabled(config) && (config.two_book_default_vat ?? config.raw?.two_book_default_vat);
        const order = super.createNewOrder({
            ...data,
            is_vat_order: data.is_vat_order ?? isVatDefault ?? false,
        });
        if (isTwoBookEnabled(config)) {
            applyTwoBookFiscalPosition(order, order.is_vat_order);
        }
        return order;
    },
});

export { applyTwoBookFiscalPosition };

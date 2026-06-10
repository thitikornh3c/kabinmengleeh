# Odoo 19 Upgrade — Tax Totals on PDF Reports

**Module:** `account` (QWeb report template)  
**Template:** `account.document_tax_totals_template`  
**Affected documents:** Sales Orders, Invoices, Purchase Orders (any report using tax totals)  
**Last updated:** June 2026

---

## Table of contents

1. [Executive summary](#executive-summary)
2. [Symptoms observed](#symptoms-observed)
3. [Root causes](#root-causes)
4. [Data structure changes (pre-19 vs Odoo 19)](#data-structure-changes-pre-19-vs-odoo-19)
5. [Legacy customizations in this repo](#legacy-customizations-in-this-repo)
6. [Withholding tax and negative amounts](#withholding-tax-and-negative-amounts)
7. [Fix options](#fix-options)
8. [Recommended approach](#recommended-approach)
9. [Implementation checklist](#implementation-checklist)
10. [QWeb reference snippet](#qweb-reference-snippet)
11. [Testing checklist](#testing-checklist)
12. [Related files](#related-files)

---

## Executive summary

After upgrading to **Odoo 19**, customized PDF tax footers may show:

- **VAT amount missing** (label visible, value blank)
- **Wrong tax labels** (e.g. Withholding Tax displayed as VAT)
- **Negative withholding tax** (e.g. `-5,100.00`) on reports

These issues are primarily caused by:

1. **Core API/template changes** in `_get_tax_totals` and `account.document_tax_totals_template`
2. **Outdated custom QWeb** still using pre-19 field names or logic
3. **Misunderstanding WHT sign** — negative WHT on Odoo forms is often **correct accounting behavior**, not a calculation bug

---

## Symptoms observed

| Symptom | Example | Likely cause |
|--------|---------|--------------|
| VAT label without amount | `VAT 7%` row empty on quotation PDF | Amount cell commented out in `same_tax_base` branch |
| WHT shown as VAT | `ภาษีมูลค่าเพิ่ม/VAT 3%` for WHT line | Hardcoded VAT prefix on all `tax_group` rows |
| Negative tax line | `Withholding Tax 3%: -5,100.00` | Tax configured to reduce payable; Odoo 19 reports actual sign |
| Totals still correct | Total = 176,800 with WHT negative | Backend math OK; display/template issue only |
| Layout unlike pre-upgrade | Missing/extra rows | Old loop over `groups_by_subtotal` no longer valid |

### Example (correct math, confusing display)

| Line | Amount (THB) |
|------|----------------|
| Untaxed Amount | 170,000.00 |
| Withholding Tax 3% | -5,100.00 |
| VAT 7% | 11,900.00 |
| **Total** | **176,800.00** |

`170,000 - 5,100 + 11,900 = 176,800` ✓

---

## Root causes

### 1. Odoo 19 redesigned tax totals for reports

Odoo centralizes tax breakdown in `_get_tax_totals()` and renders it via `account.document_tax_totals_template`.

The template now:

- Iterates `tax_totals['subtotals']` → `subtotal['tax_groups']`
- Uses monetary fields (`*_amount_currency`) with `currency` argument
- Branches on `same_tax_base` and `display_base_amount_currency`

Pre-19 custom templates that use `groups_by_subtotal`, `formatted_*` fields, or manual WHT calculation will **not work** without migration.

### 2. Custom template edits

Common mistakes after upgrade:

- Commenting out `tax_amount_currency` in the `same_tax_base` branch (VAT rows often use this branch)
- Applying one label prefix to every tax group (VAT + WHT merged visually)
- Copying old `bk_*.xml` logic that hardcodes WHT % (e.g. 1%) instead of reading from tax configuration

### 3. Withholding tax sign (not always a bug)

In Thai flows, documents often have:

- **VAT 7%** — increases total
- **Withholding Tax 3%** — reduces amount due (shown as negative)

Odoo 19 includes WHT in `tax_groups` with the sign returned by the tax engine. This matches the SO/Invoice UI.

---

## Data structure changes (pre-19 vs Odoo 19)

| Pre-19 (typical) | Odoo 19 |
|------------------|---------|
| `tax_totals['groups_by_subtotal'][subtotal_name]` | `subtotal['tax_groups']` |
| `group['tax_group_name']` | `tax_group['group_name']` |
| `group['formatted_tax_group_amount']` | `tax_group['tax_amount_currency']` + monetary widget |
| `subtotal['formatted_amount']` | `subtotal['base_amount_currency']` + monetary widget |
| `tax_totals['formatted_amount_total']` | `tax_totals['total_amount_currency']` + monetary widget |
| Sub-template `account.tax_groups_totals` | Inline loop in main template |

### Template arguments (Odoo 19)

```text
ARGUMENTS (from template docstring):
- currency: res.currency record
- tax_totals: dict from account.move._get_tax_totals (and equivalents on SO/PO)
```

### Important keys in `tax_group`

| Key | Purpose |
|-----|---------|
| `group_name` | Display name (e.g. `VAT 7%`, `Withholding Tax 3%`) |
| `tax_amount_currency` | Tax amount in document currency |
| `display_base_amount_currency` | Base amount when shown per group |
| `same_tax_base` (on `tax_totals`) | Controls which template branch renders |

---

## Legacy customizations in this repo

Backup/reference files (pre-19 style):

| File | Behavior |
|------|----------|
| `bk_amount_tax.xml` | Uses `formatted_amount`, calls `account.tax_groups_totals` |
| `bk_price_tax.html` | Hides WHT from loop; hardcodes 1% WHT; manual minus sign |

**Do not deploy these backups on Odoo 19 without migration.** Use them only as reference for required labels/layout.

---

## Withholding tax and negative amounts

### Expected behavior (Odoo 19)

- WHT reduces **amount due** → negative `tax_amount_currency` on reports is normal
- Total still includes WHT algebraically (subtract)

### Old custom behavior (`bk_price_tax.html`)

1. Loop tax groups but **skip** names containing `หัก ณ ที่จ่าย`
2. Show “Total with tax”
3. Add a **separate** WHT row with hardcoded `withholding_percent = 1`
4. Prefix amount with `-` manually

### Migration implication

| Approach | WHT % source | Sign on report |
|----------|--------------|----------------|
| Odoo 19 standard | Tax master data | From engine (often negative) |
| Old custom | Hardcoded 1% | Always manual `-` |

After upgrade, use tax configuration (3%, 1%, etc.) — do not hardcode unless business requires a fixed cosmetic layout.

---

## Fix options

### Option 1 — Inherit Odoo 19 template (recommended)

- Module inherits `account.document_tax_totals_template`
- Restore amount cell in **both** branches (`same_tax_base` and `else`)
- Conditional labels for VAT vs WHT vs other
- Keep `monetary` widget and `currency`

**Pros:** Correct amounts, maintainable  
**Cons:** Re-test on each Odoo upgrade

---

### Option 2 — Rename taxes in master data

**Path:** Accounting → Configuration → Taxes / Tax Groups

Set display names, e.g.:

- `ภาษีมูลค่าเพิ่ม/VAT 7%`
- `ภาษีหัก ณ ที่จ่าย/Withholding Tax 3%`

Template can use `tax_group['group_name']` without string hacking.

**Pros:** Minimal QWeb change  
**Cons:** WHT may still show negative

---

### Option 3 — Accept negative WHT (accounting-aligned)

No `abs()` on report — match Odoo UI.

**Pros:** Single source of truth  
**Cons:** Stakeholders may prefer positive “deduction” display

---

### Option 4 — Cosmetic positive WHT on PDF only

Use `abs()` or separate “Deduction” label in QWeb only.

**Pros:** Readable PDF  
**Cons:** Must not confuse with GL/payment amounts

---

### Option 5 — Legacy split layout (like `bk_price_tax.html`)

Filter WHT out of loop; dedicated WHT row.

**Pros:** Full layout control  
**Cons:** High maintenance; risk of wrong % or totals

---

### Option 6 — Inherit `account.tax_groups_totals`

Smaller override surface if sub-template still used in your build.

---

### Option 7 — Review tax configuration

If sign or amount is wrong **on the Odoo form** (not just PDF):

- Tax type and repartition lines
- Multiple taxes per line (VAT + WHT)
- Price included vs excluded

---

## Recommended approach

1. **Option 1** — Odoo 19 template inherit with full `tax_amount_currency` in all branches  
2. **Option 2** — Correct tax group names in master data  
3. **Option 3** — Keep negative WHT unless legal/brand requires cosmetic change (then Option 4 only for PDF)

Avoid Option 5 unless a fixed legacy PDF layout is mandatory.

---

## Implementation checklist

- [ ] Identify where custom template lives (Studio, `ir.ui.view`, or custom module)
- [ ] Compare against standard Odoo 19 `account.document_tax_totals_template`
- [ ] Remove references to `groups_by_subtotal`, `formatted_tax_group_amount`, etc.
- [ ] Uncomment / add `tax_amount_currency` monetary span in `same_tax_base` branch
- [ ] Replace global “VAT” prefix with conditional VAT / WHT / default labels
- [ ] Set tax group names in Accounting configuration
- [ ] Test SO, Invoice, PO PDFs with VAT-only and VAT+WHT lines
- [ ] Verify totals match form view (Untaxed, taxes, Total, Amount Due)
- [ ] Document module version dependency: `account` (Odoo 19)

---

## QWeb reference snippet

Conditional label (VAT vs WHT vs other) — use in both template branches:

```xml
<t t-set="group_name" t-value="tax_group.get('group_name') or ''"/>
<span t-esc="
    'ภาษีมูลค่าเพิ่ม/' + group_name
        if ('vat' in group_name.lower() or 'ภาษีมูลค่าเพิ่ม' in group_name)
    else ('ภาษีหัก ณ ที่จ่าย/' + group_name
        if ('withholding' in group_name.lower() or 'หัก ณ ที่จ่าย' in group_name)
    else group_name)
"/>
```

Amount cell (required in `same_tax_base` branch):

```xml
<td class="text-end o_price_total">
    <span class="text-nowrap"
          t-out="tax_group['tax_amount_currency']"
          t-options='{"widget": "monetary", "display_currency": currency}'/>
</td>
```

Untaxed row label (example bilingual):

```xml
<span>ราคาก่อนรวมภาษีมูลค่าเพิ่ม/Untaxed Amount</span>
```

---

## Testing checklist

| Scenario | Taxes on lines | Verify |
|----------|----------------|--------|
| VAT only | 7% VAT | Untaxed, VAT amount, Total |
| VAT + WHT | 7% + 3% WHT | WHT negative (if configured), labels correct, Total |
| Single line high amount | 7% VAT | Quotation PDF (previously missing VAT amount) |
| Paid invoice | VAT + WHT | Paid / Amount Due rows if template extended |

**Pass criteria:**

- PDF tax lines = same amounts as SO/Invoice form (within rounding)
- No tax group mislabeled as VAT when it is WHT
- Total = Untaxed + sum(tax groups) + rounding (if any)

---

## Related files

| Path | Description |
|------|-------------|
| `docs/odoo19-tax-report-upgrade.md` | This document |
| `bk_amount_tax.xml` | Pre-19 backup (formatted fields) |
| `bk_price_tax.html` | Pre-19 backup (manual WHT 1%) |

---

## Appendix — Thai summary (สรุปภาษาไทย)

**อาการหลัก:** VAT ไม่ขึ้นตัวเลข, WHT โผล่เป็น VAT, WHT ติดลบ  
**สาเหตุ:** โครง `tax_totals` เปลี่ยนใน Odoo 19 + template custom ผิด branch / hardcode label  
**WHT ติดลบ:** มักถูกต้องตามระบบ (ลดยอดจ่าย) ไม่ใช่บั๊กคำนวณ  
**แนวทางแก้ที่แนะนำ:** inherit template 19 + ตั้งชื่อ tax ใน master + ยอมรับเครื่องหมายลบ WHT (หรือแก้ cosmetic ใน PDF เท่านั้น)

---

## Revision history

| Date | Change |
|------|--------|
| 2026-06 | Initial document from upgrade troubleshooting (tax totals / WHT / VAT PDF) |

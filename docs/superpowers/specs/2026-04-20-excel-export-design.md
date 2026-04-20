# Excel Export — Design Spec

**Date:** 2026-04-20
**Tool:** `project_revenue.html` (single-file HTML tool for May–October revenue projections)
**Reference file:** `/Users/lucasknowles/Downloads/Reference Projection Sheet.xlsx`
**Status:** Approved — ready for implementation plan

---

## Purpose

Add a "Download Excel" export to the HTML tool. The exported `.xlsx` takes the projected monthly revenue (already computed by the tool) and layers on top a full pro-forma that shows operating costs (booking fees, turnover charges) and the split between Grand Welcome's management share and the homeowner's net take.

The exported workbook is designed to be sent to prospective homeowners alongside the existing chart PNG. Owners receive a live spreadsheet they can tweak (not a static summary), with every downstream value driven by formulas so they can see how changes to occupancy, ADR, turnover cost, or management rate flow through to net income.

## In-scope / out-of-scope

**In scope:**
- New "Download Excel" button on the existing HTML tool.
- Three new form inputs: Turnover Charge ($), Booking Fee (%), Management Rate (%).
- Single-sheet `.xlsx` file mirroring the reference workbook's layout, formulas, and styling exactly.
- External-facing rename: Soft/Mid/Strong → Base/Strong/High on the on-screen preview table, communication paragraph, chart PNG labels, markdown export, and Excel export.

**Out of scope:**
- Python CLI changes (`project_revenue.py`): form prompts stay Soft/Mid/Strong.
- HTML form input labels: stay Soft/Mid/Strong (internal terminology).
- README rewrites.
- Multi-sheet workbooks, charts embedded in the sheet, or scenario-comparison views.
- Per-scenario turnover charges, per-month management rate overrides, or bedroom-scaled operating-cost defaults.

## User inputs (added to main form)

Three new fields in a "Pro forma inputs" subgroup beneath the existing Peak ADR inputs:

| Field ID | Label | Default | Placeholder | Validation |
|---|---|---|---|---|
| `turnover_charge` | Turnover Charge ($) | blank | `e.g. 5500` | Positive integer. Required to enable Excel export. |
| `booking_fee_pct` | Booking Fee (%) | `16.5` | — | Positive number, 0–100. |
| `mgmt_rate_pct` | Management Rate (%) | `20.0` | — | Positive number, 0–100. |

None of these are required to run the on-screen projection. They gate only the **Download Excel** button: if Turnover Charge is blank, the button is disabled with a tooltip `Enter a turnover charge to enable Excel export.`

### Turnover charge semantics

The turnover charge is a single dollar value that represents the total seasonal turnover cost collected from guests and paid through to third-party vendors (cleaners, inspectors, stocking). In the exported workbook it appears twice:

- **Row 23** (Turnover Charge Collected from Guest): positive `$N` — revenue collected from guests at booking.
- **Row 29** (Turnover Costs): `=-G23` — paid out to vendors.

Net effect on rental profit is zero — it passes through. The label on row 23 includes the static note `(approximately 20 guest stays)` per the reference.

## Rename scope — Base / Strong / High

**Internal surfaces (unchanged — stay Soft / Mid / Strong):**
- HTML form field labels (`Peak Jul/Aug ADR — Soft/Mid/Strong ($)`)
- Python CLI prompts and on-screen output
- Internal variable names in the code

**External surfaces (renamed to Base / Strong / High):**
- HTML on-screen preview table headers and body
- Communication paragraph (the Section 7 copy, both CLI print and HTML "Copy paragraph")
- Chart PNG legend and scenario labels
- Markdown export (downloaded by "Download markdown" button)
- Excel export (every occurrence)

**Mapping:**

| Internal (input) | External (output) | Numeric |
|---|---|---|
| Soft | Base | 80% of peak |
| Mid | Strong | 100% of peak |
| Strong | High | 130% of peak |

Note: The external "Strong" label refers to the *central / expected* scenario (what the owner should plan around), not the upside. The reframing intentionally treats Base as the conservative commit, Strong as typical performance, and High as the ceiling.

## Workbook structure

**Sheet:** Single sheet named `{N}-Bedroom` (e.g. `3-Bedroom`, `5+-Bedroom`).

**File name:** `projection_{sanitizedLabel}_{YYYYMMDD}.xlsx` — matches existing markdown/PNG convention.

### Layout

Transcribes the reference workbook 1:1. Column widths, merged-cell ranges, fills, fonts, number formats, and row content all match the reference.

**Rows 1–2 — Title block**
- A1 (merged A1:I1): `{Property Label} – {N}-Bedroom Revenue Projection` — bold size 14
- A2 (merged A2:I2): `Year 3+ Projection | May – October Season  |  Base / Strong / High Market Scenarios` — bold size 10

**Row 4 — Projection table headers** (fill `FF1F3864` dark navy, white text):
- A4: `Month`, B4: `Occ`, C4: `Nights`, D4: `Base ADR`, E4: `Base Revenue`, F4: `Strong ADR`, G4: `Strong Revenue`, H4: `High ADR`, I4: `High Revenue`

**Rows 5–10 — May through October** (one row per month):
- A: Month name
- B: Occupancy decimal (format `0%`)
- C: `={days_in_month}*B{row}` (format `0.0`)
- D, F, H: ADR values (raw numbers, format `\$#,##0`)
- E, G, I: Revenue formulas `=D{row}*C{row}` etc. (format `\$#,##0;"($"#,##0);"$-"`)

Occupancy and ADR values come from the current projection state (already computed by the tool via the same math used for the on-screen table). Base column pulls from Soft, Strong from Mid, High from Strong.

**Row 11 — TOTAL** (fill `FFE8EEF7`, bold):
- A: `TOTAL`
- C: `=SUM(C5:C10)`
- E, G, I: `=SUM(column)`

**Row 12 — helper label:**
- B12: `(Occupancy) `

**Row 13 — Management Rate** (the single source of truth for downstream formulas):
- A13 (merged A13:F13): `Management Rate`
- G13 (merged G13:I13): decimal (e.g. `0.20`), format `0.0%`, fill `FFDAEEF3` cyan, bold

**Row 14 — explainer footnote** (merged A14:I14, italic, size 9):
> `     ↳ Grand Welcome's management rate as a percentage of rental profit. Adjust for this specific home's agreement.`

**Rows 17–18 — Pro forma section header:**
- A17: `{N}-Bedroom Pro Forma` (bold size 14)
- A18 (merged A18:I18): `How a season's reservations distribute — Base / Strong / High` (note: updated from reference which said "Soft / Mid / Strong")

**Row 20 — Pro forma column headers** (fill `FF1F3864`):
- A20: `Line Item`, G20: `Base`, H20: `Strong`, I20: `High`

**Row 21 — GUEST PAYMENT COLLECTED** (merged A21:F21, fill `FFD9E2F3`, bold)

**Row 22 — Nightly Rental Fare:**
- G22: `=E11`, H22: `=G11`, I22: `=I11`

**Row 23 — Turnover Charge Collected from Guest:**
- A23 (merged A23:F23): `Turnover Charge Collected from Guest  (approximately 20 guest stays)`
- G23, H23, I23: user-supplied turnover value (raw number)

**Row 24 — Total Paid by Guest** (fill `FFE8EEF7`, bold):
- G24: `=G22+G23`, H24: `=H22+H23`, I24: `=I22+I23`

**Row 26 — OPERATING COSTS** (merged A26:F26, fill `FFD9E2F3`, bold):
> `OPERATING COSTS   (Charged to Guests, Paid to Third Parties)`

**Row 27 — Website & Advertising Costs:**
- G27: `=-G24*{bookingFeeDecimal}`, H27: `=-H24*{bookingFeeDecimal}`, I27: `=-I24*{bookingFeeDecimal}`
- The booking-fee percentage is **baked into the formula as a constant** (e.g. `=-G24*0.165`), not stored in a separate cell. Keeps the sheet uncluttered; the booking fee is not something owners typically negotiate.

**Row 28 — explainer footnote** (merged A28:I28):
> `     ↳ Charged by Airbnb, VRBO, and Meta Ads, plus credit card processors. A standard cost of booking a vacation rental on any major platform — applies to every property listed on these channels, regardless of who manages it.`

**Row 29 — Turnover Costs:**
- G29: `=-G23`, H29: `=-H23`, I29: `=-I23`

**Row 30 — explainer footnote** (merged A30:I30):
> `     ↳ Charged by the vendors who service the home between guests — cleaners, inspectors, and stocking services. A standard cost of any professionally operated vacation rental.`

**Row 31 — Total Operating Costs** (fill `FFE8EEF7`, bold):
- G31: `=G27+G29`, H31: `=H27+H29`, I31: `=I27+I29`

**Row 33 — Rental Profit** (fill `FFE8EEF7`, bold):
- A33 (merged A33:F33): `Rental Profit   (what remains after the home's operating costs)`
- G33: `=G24+G31`, H33: `=H24+H31`, I33: `=I24+I31`

**Row 35 — GRAND WELCOME MANAGEMENT** (merged A35:F35, fill `FFD9E2F3`, bold)

**Row 36 — Management Rate line:**
- A36 (merged A36:F36): `="Management Rate  ("&TEXT($G$13,"0%")&" of rental profit)"` — formula reads G13 so label stays in sync
- G36: `=-(G33)*$G$13`, H36: `=-(H33)*$G$13`, I36: `=-(I33)*$G$13`

**Row 37 — explainer footnote** (merged A37:I37):
> `     ↳ Like any business, the home covers its operating costs first. What remains is rental profit — shared between the homeowner and Grand Welcome for managing the property (marketing, booking management, guest communication, pricing optimization, owner reporting, 24/7 operational support). The majority flows to the homeowner.`

**Row 39 — NET TO HOMEOWNER** (fill `FFC8E0C8` green, bold size 11):
- A39 (merged A39:F39): `NET TO HOMEOWNER`
- G39: `=G33+G36`, H39: `=H33+H36`, I39: `=I33+I36`

**Rows 42–43 — HOW TO READ THIS REPORT:**
- A42 (merged A42:I42, fill `FFD9E2F3`, bold): `HOW TO READ THIS REPORT`
- A43 (merged A43:I43, wrap text, size 9): three-paragraph explainer, verbatim from reference, with `Soft / Mid / Strong` replaced by `Base / Strong / High`.

### Styling tokens

| Token | Hex | Used on |
|---|---|---|
| Header navy | `FF1F3864` | Row 4 (projection headers), Row 20 (pro forma headers) |
| Section blue | `FFD9E2F3` | Rows 21, 26, 35, 42 |
| Subtotal blue | `FFE8EEF7` | Rows 11, 24, 31, 33 |
| Green | `FFC8E0C8` | Row 39 |
| Editable cyan | `FFDAEEF3` | Row 13 (G13 only) |

**Number formats:**
- ADR: `\$#,##0`
- Revenue / currency: `\$#,##0;"($"#,##0\);"$-"` (negatives in parens)
- Occupancy (row 5–10, col B): `0%`
- Management rate (G13): `0.0%`
- Nights (col C): `0.0`

**Column widths:** A=52, B=11, C=default, D=12, E=13, F=12, G=14.33, H=12, I=16.66

## Integration

### Library

ExcelJS 4.x loaded via CDN:

```html
<script src="https://cdnjs.cloudflare.com/ajax/libs/exceljs/4.4.0/exceljs.min.js"></script>
```

Pinned to an exact version (per supply-chain standard). If the CDN fails to load, the Excel button shows an alert on click: `Excel library failed to load — check your internet connection and refresh.`

### Button

New `<button id="download-excel" type="button" class="primary">Download Excel</button>` inserted in the export button row, after "Download chart PNG." Same primary styling as the chart PNG button to signal it's a first-class output.

**Disabled states:**
- No projection yet (`lastState` empty): disabled, no tooltip (matches other export buttons' behavior).
- Projection exists but Turnover Charge input is blank: disabled with tooltip `Enter a turnover charge to enable Excel export.`

### Code shape

Two new functions in the existing `<script>` block:

```javascript
function buildWorkbook(state, turnover, bookingFeePct, mgmtRatePct) {
  // Returns an ExcelJS Workbook with one worksheet matching the layout above.
  // Pure function — no side effects, fully driven by inputs.
}

async function downloadExcel() {
  // Reads form inputs, validates, calls buildWorkbook, triggers download via blob.
}
```

`downloadExcel` is wired to the button's click handler alongside the existing `downloadMarkdown` / `downloadChartPNG` handlers.

### Failure modes

| Failure | Behavior |
|---|---|
| ExcelJS CDN didn't load | Alert on click, button stays enabled (so user can retry after refresh). |
| Turnover Charge blank or non-numeric | Button disabled; inline validation message under the field if user tries to submit with a bad value. |
| Booking Fee or Management Rate blank | Falls back to defaults (16.5 / 20.0). |
| Browser blocks download | Fall through to ExcelJS's default error; alert with manual instructions. |

## File touch points

- `project_revenue.html` — only file modified. Approximate changes:
  - `<head>`: +1 line (ExcelJS CDN script tag).
  - Form HTML: +~25 lines (three new input fields in a subgroup).
  - Button row HTML: +1 line (Download Excel button).
  - Preview table template + paragraph generation: string replacements for scenario labels (Soft→Base, Mid→Strong, Strong→High) — but only in the output rendering functions, not in the state model.
  - New JS: `buildWorkbook()` (~150 lines), `downloadExcel()` (~30 lines), disabled-state wiring (~10 lines).

No changes to `project_revenue.py`, `README.md`, or any other file.

## Success criteria

1. User fills the existing form + three new inputs → clicks "Download Excel" → gets an `.xlsx` file.
2. Opening the file in Excel/Numbers/Google Sheets renders identically to the reference workbook (same styling, same formulas, same merged cells).
3. Changing a cell value in the opened spreadsheet (e.g. occupancy in B7) recomputes every downstream cell automatically.
4. Changing G13 (management rate) updates both the row 36 label and the values in one step.
5. The HTML on-screen preview, chart PNG, markdown export, and Excel export all use Base / Strong / High consistently.
6. Python CLI prompts still say Soft/Mid/Strong (verified by running the script).

## Non-goals

- No programmatic validation that the Excel formulas produce the same totals as the HTML's in-memory calculation. The spreadsheet is self-validating once opened.
- No automated test of the .xlsx file structure. Manual spot-check against the reference is the validation method.
- No preservation of the editorial-chart work from earlier in the session (already reverted).

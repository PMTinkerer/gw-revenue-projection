# Excel Export Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a "Download Excel" button to `project_revenue.html` that exports a live-formula `.xlsx` pro-forma matching the reference workbook at `/Users/lucasknowles/Downloads/Reference Projection Sheet.xlsx`.

**Architecture:** Single-file HTML tool. ExcelJS loaded via CDN builds an in-memory workbook from the existing projection state plus three new user inputs (Turnover Charge, Booking Fee %, Management Rate %). Download triggered via blob URL. External-facing labels flip from Soft/Mid/Strong to Base/Strong/High across the preview table, chart PNG, markdown export, and Excel export; internal form labels stay Soft/Mid/Strong.

**Tech Stack:** Vanilla JS, ExcelJS 4.4.0 via CDN (`cdnjs.cloudflare.com`). Verification via Python + Playwright + openpyxl (already installed locally from prior chart-verification work).

**Spec:** `docs/superpowers/specs/2026-04-20-excel-export-design.md`

**Project root:** `/Users/lucasknowles/gw-revenue-projection/`

**Working directory for all `git` commands:** `/Users/lucasknowles/gw-revenue-projection/` (standalone repo, no remote).

---

## File Structure

All work happens in **one file**: `/Users/lucasknowles/gw-revenue-projection/project_revenue.html` (currently 796 lines).

| Zone | Lines (current) | Change |
|---|---|---|
| `<head>` | 3–61 | +1 line: ExcelJS `<script src="...">` tag |
| Preview table `<thead>` | 137–142 | Rename column headers Soft/Mid/Strong → Base/Strong/High |
| Form grid | 71–115 | +3 new inputs in a subgroup |
| Actions block after chart | 177–180 | +1 Download Excel button |
| Chart footer note | 181–184 | Rename Soft/Mid/Strong → Base/Strong/High |
| Chart subtitle | 422 | Rename |
| Chart legend | 480–484 | Rename |
| Chart sidebar cards | 565–569 | Rename |
| Chart footer text | 601–604 | Rename |
| Markdown export | 673–704 | Rename in labels + column headers |
| JS: new functions | end of script | `buildWorkbook()` + `downloadExcel()` + disabled-state wiring |

Verification artifact created under `/Users/lucasknowles/gw-revenue-projection/scripts/` (new directory) — not part of the shipped tool, just a reproducible check.

---

## Task 1: Add ExcelJS CDN script tag

**Files:**
- Modify: `project_revenue.html:3-7` (the `<head>` block)

**Why:** Load ExcelJS before any JS runs so `window.ExcelJS` exists when the Download Excel handler is invoked. Pin to exact version 4.4.0 per supply-chain standard. Use `defer` so it loads in parallel with parsing and doesn't block rendering.

- [ ] **Step 1: Insert the script tag**

Edit `project_revenue.html`. Between the existing `<title>` line and the `<style>` block, add the ExcelJS CDN tag:

```html
<title>GW Revenue Projection — May–Oct (v1.0)</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/exceljs/4.4.0/exceljs.min.js" defer></script>
<style>
```

- [ ] **Step 2: Verify ExcelJS loads in the browser**

Open the HTML file in a browser (`open /Users/lucasknowles/gw-revenue-projection/project_revenue.html`). Open DevTools → Console. Type:
```
typeof ExcelJS
```
Expected: `"object"`. If `"undefined"`, the CDN URL is wrong or network failed.

- [ ] **Step 3: Commit**

```bash
cd /Users/lucasknowles/gw-revenue-projection
git add project_revenue.html
git commit -m "Add ExcelJS 4.4.0 CDN for upcoming .xlsx export"
```

---

## Task 2: Rename external labels Soft/Mid/Strong → Base/Strong/High

**Files:**
- Modify: `project_revenue.html` — preview table header (lines 137–142), chart drawing (lines 422, 480–484, 565–569, 601–604), chart footer HTML (line 183), markdown builder (lines 673–704)

**Why:** Do the rename before building the Excel feature so new code uses the external labels consistently. Per spec: form labels stay Soft/Mid/Strong, but everything the owner sees (preview table, chart PNG, markdown, and the upcoming Excel) uses Base/Strong/High.

**Mapping:** Soft → Base · Mid → Strong · Strong → High

- [ ] **Step 1: Update preview table column headers**

Current `project_revenue.html:137-142`:

```html
<tr>
  <th>Month</th><th>Occ</th><th>Nights</th>
  <th>Soft ADR</th><th>Soft Rev</th>
  <th>Mid ADR</th><th>Mid Rev</th>
  <th>Strong ADR</th><th>Strong Rev</th>
</tr>
```

Replace with:

```html
<tr>
  <th>Month</th><th>Occ</th><th>Nights</th>
  <th>Base ADR</th><th>Base Rev</th>
  <th>Strong ADR</th><th>Strong Rev</th>
  <th>High ADR</th><th>High Rev</th>
</tr>
```

- [ ] **Step 2: Update chart canvas subtitle**

Current `project_revenue.html:422`:

```js
const subtitle = `${bucket.toUpperCase()} home  ·  Soft / Mid / Strong market scenarios`;
```

Replace with:

```js
const subtitle = `${bucket.toUpperCase()} home  ·  Base / Strong / High market scenarios`;
```

- [ ] **Step 3: Update chart legend items**

Current `project_revenue.html:480-484`:

```js
const legendItems = [
  { label: "Soft",   color: PALETTE.brandLight },
  { label: "Mid",    color: PALETTE.brand },
  { label: "Strong", color: PALETTE.brandDark },
];
```

Replace with:

```js
const legendItems = [
  { label: "Base",   color: PALETTE.brandLight },
  { label: "Strong", color: PALETTE.brand },
  { label: "High",   color: PALETTE.brandDark },
];
```

- [ ] **Step 4: Update chart sidebar total cards**

Current `project_revenue.html:565-569`:

```js
const cards = [
  { label: "Soft",   value: con.total,  fg: PALETTE.brandDark, bg: PALETTE.brandLight },
  { label: "Mid",    value: cenS.total, fg: "#FFFFFF",         bg: PALETTE.brand },
  { label: "Strong", value: strS.total, fg: "#FFFFFF",         bg: PALETTE.brandDark },
];
```

Replace with:

```js
const cards = [
  { label: "Base",   value: con.total,  fg: PALETTE.brandDark, bg: PALETTE.brandLight },
  { label: "Strong", value: cenS.total, fg: "#FFFFFF",         bg: PALETTE.brand },
  { label: "High",   value: strS.total, fg: "#FFFFFF",         bg: PALETTE.brandDark },
];
```

- [ ] **Step 5: Update chart footer disclaimer**

Current `project_revenue.html:601-604`:

```js
ctx.fillText(
  "Soft · Mid · Strong reflect market-condition scenarios — not forecasts or commitments.",
  70, H - 48
);
```

Replace with:

```js
ctx.fillText(
  "Base · Strong · High reflect market-condition scenarios — not forecasts or commitments.",
  70, H - 48
);
```

- [ ] **Step 6: Update HTML footer note under chart preview**

Current `project_revenue.html:182-184`:

```html
<div class="footer-note">
  Chart modeled on a mature listing with 3+ years of established reviews.
  Soft · Mid · Strong reflect market-condition scenarios — not forecasts or commitments.
</div>
```

Replace with:

```html
<div class="footer-note">
  Chart modeled on a mature listing with 3+ years of established reviews.
  Base · Strong · High reflect market-condition scenarios — not forecasts or commitments.
</div>
```

- [ ] **Step 7: Update markdown builder — peak ADR label block**

Current `project_revenue.html:672-679`:

```js
if (haircut) {
  L.push(`- Soft: ${adrFmt(conEntered)} entered → **${adrFmt(conUsed)} used** ` +
         `(acquisition_underwriting 10% haircut applied per Section 7)`);
} else {
  L.push(`- Soft: ${adrFmt(conUsed)}`);
}
L.push(`- Mid: ${adrFmt(cen)}`);
L.push(`- Strong: ${adrFmt(strch)}`);
```

Replace with:

```js
if (haircut) {
  L.push(`- Base: ${adrFmt(conEntered)} entered → **${adrFmt(conUsed)} used** ` +
         `(acquisition_underwriting 10% haircut applied per Section 7)`);
} else {
  L.push(`- Base: ${adrFmt(conUsed)}`);
}
L.push(`- Strong: ${adrFmt(cen)}`);
L.push(`- High: ${adrFmt(strch)}`);
```

- [ ] **Step 8: Update markdown builder — monthly table header**

Current `project_revenue.html:683-684`:

```js
L.push("| Month | Occ | Nights | Soft ADR | Soft Rev | Mid ADR | Mid Rev | Strong ADR | Strong Rev |");
L.push("|-------|----:|-------:|---------:|---------:|--------:|--------:|-----------:|-----------:|");
```

Replace with:

```js
L.push("| Month | Occ | Nights | Base ADR | Base Rev | Strong ADR | Strong Rev | High ADR | High Rev |");
L.push("|-------|----:|-------:|---------:|---------:|-----------:|-----------:|---------:|---------:|");
```

- [ ] **Step 9: Update markdown builder — context disclaimer**

Current `project_revenue.html:702`:

```js
L.push("- Soft · Mid · Strong reflect market-condition scenarios — not forecasts or commitments.");
```

Replace with:

```js
L.push("- Base · Strong · High reflect market-condition scenarios — not forecasts or commitments.");
```

- [ ] **Step 10: Verify the rename in a browser**

Open the HTML file. Fill the form: Label=`Test`, Bucket=`3br`, Use case=`owner_onboarding`, Mid peak=`1000`, leave Soft/Strong blank. Click Project revenue.

Verify:
- Preview table column headers read `Base ADR | Base Rev | Strong ADR | Strong Rev | High ADR | High Rev`
- Chart canvas legend shows `Base · Strong · High`
- Chart canvas sidebar cards show `BASE · STRONG · HIGH`
- Chart footer reads `Base · Strong · High reflect market-condition scenarios...`
- Click "Download markdown" — in the downloaded file, peak ADRs section uses `Base/Strong/High` and the monthly table header uses `Base/Strong/High`.

Confirm the form input labels are **unchanged** (still say "Peak Jul/Aug ADR — Soft / Mid / Strong").

- [ ] **Step 11: Commit**

```bash
cd /Users/lucasknowles/gw-revenue-projection
git add project_revenue.html
git commit -m "Rename external labels Soft/Mid/Strong to Base/Strong/High

Form inputs keep the internal Soft/Mid/Strong terminology.
Preview table, chart PNG, and markdown export now use
Base/Strong/High to frame scenarios externally.
Note: external Strong now refers to the central/expected
scenario (was Mid); external High is the upside (was Strong)."
```

---

## Task 3: Add three new form inputs

**Files:**
- Modify: `project_revenue.html:71-115` (the `.grid` form section)

**Why:** The Turnover Charge, Booking Fee, and Management Rate inputs live on the main form per the design decision. Defaults: Booking Fee 16.5%, Management Rate 20.0%, Turnover Charge blank (required to enable Excel export).

- [ ] **Step 1: Insert three new input divs at the end of the form grid**

Current `project_revenue.html:110-115` (end of the `.grid` block):

```html
        <div>
          <label for="peak_stretch">Peak Jul/Aug ADR — Strong ($)</label>
          <input id="peak_stretch" type="number" step="1" min="1" placeholder="blank = 130% of Mid" />
          <div class="hint">Optional. Defaults to 130% of Mid.</div>
        </div>
      </div>
```

Replace with:

```html
        <div>
          <label for="peak_stretch">Peak Jul/Aug ADR — Strong ($)</label>
          <input id="peak_stretch" type="number" step="1" min="1" placeholder="blank = 130% of Mid" />
          <div class="hint">Optional. Defaults to 130% of Mid.</div>
        </div>

        <div>
          <label for="turnover_charge">Turnover Charge ($)</label>
          <input id="turnover_charge" type="number" step="1" min="0" placeholder="e.g. 5500" />
          <div class="hint">Total seasonal turnover cost collected from guests. Required for Excel export.</div>
        </div>

        <div>
          <label for="booking_fee_pct">Booking Fee (%)</label>
          <input id="booking_fee_pct" type="number" step="0.1" min="0" max="100" value="16.5" />
          <div class="hint">Airbnb, VRBO, Meta Ads, and card processors. Default 16.5%.</div>
        </div>

        <div>
          <label for="mgmt_rate_pct">Management Rate (%)</label>
          <input id="mgmt_rate_pct" type="number" step="0.1" min="0" max="100" value="20.0" />
          <div class="hint">Grand Welcome's share of rental profit. Default 20%.</div>
        </div>
      </div>
```

- [ ] **Step 2: Verify the form renders correctly**

Open the HTML file. Confirm:
- Three new fields appear in the grid below "Peak Jul/Aug ADR — Strong"
- Booking Fee shows `16.5` pre-filled
- Management Rate shows `20.0` pre-filled
- Turnover Charge is empty with `e.g. 5500` placeholder
- The grid layout (two columns on desktop, one on mobile) is unchanged

- [ ] **Step 3: Commit**

```bash
cd /Users/lucasknowles/gw-revenue-projection
git add project_revenue.html
git commit -m "Add Turnover/Booking Fee/Management Rate inputs to form

Turnover is blank by default (required to enable Excel export).
Booking Fee defaults to 16.5%, Management Rate to 20.0%."
```

---

## Task 4: Add Download Excel button (handler not wired yet)

**Files:**
- Modify: `project_revenue.html:177-180` (the actions block under the chart card)

**Why:** Put the button in the DOM before the handler so the disabled-state wiring in Task 9 has something to point at. Placing it next to "Download chart PNG" signals it's a first-class export.

- [ ] **Step 1: Add the Excel button to the actions row**

Current `project_revenue.html:177-180`:

```html
<div class="actions">
  <button id="download-png" type="button" class="primary">Download chart PNG</button>
  <button id="copy-png" type="button">Copy image to clipboard</button>
</div>
```

Replace with:

```html
<div class="actions">
  <button id="download-png" type="button" class="primary">Download chart PNG</button>
  <button id="copy-png" type="button">Copy image to clipboard</button>
  <button id="download-xlsx" type="button" class="primary" disabled
          title="Enter a turnover charge to enable Excel export.">Download Excel</button>
</div>
```

- [ ] **Step 2: Verify**

Open the HTML file. Run a projection. Confirm the Download Excel button appears, is grayed out (disabled), and hovering shows the tooltip text.

- [ ] **Step 3: Commit**

```bash
cd /Users/lucasknowles/gw-revenue-projection
git add project_revenue.html
git commit -m "Add Download Excel button to export actions (disabled)"
```

---

## Task 5: Implement `buildWorkbook()` — skeleton, widths, title, projection headers

**Files:**
- Modify: `project_revenue.html` — new JS code inserted before the final `</script>` tag (current line 794)

**Why:** Start the workbook builder with structural scaffolding: the worksheet, column widths, title rows, and projection-table header row. Each subsequent task appends more rows to the same function. Splitting by row-range is the natural decomposition because the reference workbook is laid out as sequential blocks.

- [ ] **Step 1: Add helper constants and the function skeleton**

Find line 721 in `project_revenue.html` (the blank line right before `// ----` `Form handling` section). Insert the following block **before** the "Form handling" comment:

```js
// ---------------------------------------------------------------------------
// Excel export (ExcelJS)
// ---------------------------------------------------------------------------
const XLSX_STYLES = {
  // Fills
  headerNavy:    { type: "pattern", pattern: "solid", fgColor: { argb: "FF1F3864" } },
  sectionBlue:   { type: "pattern", pattern: "solid", fgColor: { argb: "FFD9E2F3" } },
  subtotalBlue:  { type: "pattern", pattern: "solid", fgColor: { argb: "FFE8EEF7" } },
  netGreen:      { type: "pattern", pattern: "solid", fgColor: { argb: "FFC8E0C8" } },
  editableCyan:  { type: "pattern", pattern: "solid", fgColor: { argb: "FFDAEEF3" } },
  // Fonts
  whiteBold10:   { bold: true, size: 10, color: { argb: "FFFFFFFF" } },
  bold10:        { bold: true, size: 10 },
  bold11:        { bold: true, size: 11 },
  bold14:        { bold: true, size: 14 },
  normal10:      { bold: false, size: 10 },
  italic9:       { italic: true, size: 9 },
  // Number formats
  fmtCurrency:   '"$"#,##0;"($"#,##0");""$-"',
  fmtAdr:        '"$"#,##0',
  fmtPct0:       "0%",
  fmtPct1:       "0.0%",
  fmtNights:     "0.0",
};

// Map the bedroom bucket key to a sheet-name-safe label.
function bucketSheetName(bucket) {
  // Excel sheet names can't contain: : \ / ? * [ ]  and must be <= 31 chars.
  switch (bucket) {
    case "1-2br": return "1-2 Bedroom";
    case "3br":   return "3-Bedroom";
    case "4br":   return "4-Bedroom";
    case "5+br":  return "5+ Bedroom";
    default:      return "Projection";
  }
}

// Return the N-Bedroom phrase used in titles ("3-Bedroom", "5+ Bedroom", etc.).
function bucketTitlePhrase(bucket) {
  return bucketSheetName(bucket);
}

function buildWorkbook(state, turnover, bookingFeePct, mgmtRatePct) {
  const { label, bucket, _computed } = state;
  const { con, cenS, strS } = _computed;
  const sheetName = bucketSheetName(bucket);
  const titlePhrase = bucketTitlePhrase(bucket);

  const wb = new ExcelJS.Workbook();
  wb.creator = "GW Revenue Projection Tool";
  wb.created = new Date();
  const ws = wb.addWorksheet(sheetName);

  // Column widths (match reference)
  ws.columns = [
    { width: 52 },    // A
    { width: 11 },    // B
    { width: 9 },     // C (default-ish)
    { width: 12 },    // D
    { width: 13 },    // E
    { width: 12 },    // F
    { width: 14.33 }, // G
    { width: 12 },    // H
    { width: 16.66 }, // I
  ];

  // ---- Row 1: Title ------------------------------------------------------
  ws.mergeCells("A1:I1");
  const c1 = ws.getCell("A1");
  c1.value = `${label} – ${titlePhrase} Revenue Projection`;
  c1.font = { bold: true, size: 14 };
  c1.alignment = { horizontal: "left", vertical: "middle" };

  // ---- Row 2: Subtitle ---------------------------------------------------
  ws.mergeCells("A2:I2");
  const c2 = ws.getCell("A2");
  c2.value = "Year 3+ Projection | May – October Season  |  Base / Strong / High Market Scenarios";
  c2.font = { bold: true, size: 10 };
  c2.alignment = { horizontal: "left", vertical: "middle" };

  // ---- Row 4: Projection table header -----------------------------------
  const hdr = ["Month", "Occ", "Nights", "Base ADR", "Base Revenue",
               "Strong ADR", "Strong Revenue", "High ADR", "High Revenue"];
  const r4 = ws.getRow(4);
  hdr.forEach((h, i) => {
    const cell = r4.getCell(i + 1);
    cell.value = h;
    cell.font = XLSX_STYLES.whiteBold10;
    cell.fill = XLSX_STYLES.headerNavy;
    cell.alignment = { horizontal: i === 0 ? "left" : "right", vertical: "middle" };
  });

  return wb;
}
```

- [ ] **Step 2: Verify the skeleton compiles**

Open the HTML file. Open DevTools → Console. Paste:

```js
const fakeState = {
  label: "Test Home",
  bucket: "3br",
  _computed: { con: { rows: [], total: 0 }, cenS: { rows: [], total: 0 }, strS: { rows: [], total: 0 } }
};
const wb = buildWorkbook(fakeState, 5500, 16.5, 20);
wb.xlsx.writeBuffer().then(buf => console.log("wrote", buf.byteLength, "bytes"));
```

Expected: console prints `wrote N bytes` where N is a few thousand. No errors.

- [ ] **Step 3: Commit**

```bash
cd /Users/lucasknowles/gw-revenue-projection
git add project_revenue.html
git commit -m "Scaffold buildWorkbook() with title rows, column widths, headers"
```

---

## Task 6: Implement projection table body + TOTAL + management rate

**Files:**
- Modify: `project_revenue.html` — extend `buildWorkbook()` with rows 5–14

**Why:** Fill in the monthly rows with live `=days*Occ` and `=ADR*Nights` formulas, the `=SUM()` total row, and the management rate cell (G13) that downstream formulas reference. After this task the top section of the workbook matches the reference exactly.

- [ ] **Step 1: Append rows 5–14 to `buildWorkbook()`**

Find the `return wb;` line at the end of `buildWorkbook()` (added in Task 5). Insert the following code **before** `return wb;`:

```js
  // ---- Rows 5-10: Monthly projection ------------------------------------
  const MONTHS_DAYS = [
    { m: "May", days: 31 },
    { m: "Jun", days: 30 },
    { m: "Jul", days: 31 },
    { m: "Aug", days: 31 },
    { m: "Sep", days: 30 },
    { m: "Oct", days: 31 },
  ];
  for (let i = 0; i < 6; i++) {
    const rowNum = 5 + i;
    const r = ws.getRow(rowNum);
    const { m, days } = MONTHS_DAYS[i];
    // Source data (pulled from projection state, indexed 0..5).
    const occ   = con.rows[i].occupancy;      // same across scenarios
    const conA  = con.rows[i].adr;
    const cenA  = cenS.rows[i].adr;
    const strA  = strS.rows[i].adr;

    r.getCell(1).value = m;
    r.getCell(1).font = XLSX_STYLES.normal10;

    r.getCell(2).value = occ;
    r.getCell(2).numFmt = XLSX_STYLES.fmtPct0;
    r.getCell(2).font = XLSX_STYLES.normal10;
    r.getCell(2).alignment = { horizontal: "right" };

    r.getCell(3).value = { formula: `${days}*B${rowNum}` };
    r.getCell(3).numFmt = XLSX_STYLES.fmtNights;
    r.getCell(3).font = XLSX_STYLES.normal10;
    r.getCell(3).alignment = { horizontal: "right" };

    // Base (Soft in the calc)
    r.getCell(4).value = Math.round(conA);
    r.getCell(4).numFmt = XLSX_STYLES.fmtAdr;
    r.getCell(4).font = XLSX_STYLES.normal10;
    r.getCell(5).value = { formula: `D${rowNum}*C${rowNum}` };
    r.getCell(5).numFmt = XLSX_STYLES.fmtCurrency;
    r.getCell(5).font = XLSX_STYLES.normal10;

    // Strong (Mid in the calc)
    r.getCell(6).value = Math.round(cenA);
    r.getCell(6).numFmt = XLSX_STYLES.fmtAdr;
    r.getCell(6).font = XLSX_STYLES.normal10;
    r.getCell(7).value = { formula: `F${rowNum}*C${rowNum}` };
    r.getCell(7).numFmt = XLSX_STYLES.fmtCurrency;
    r.getCell(7).font = XLSX_STYLES.normal10;

    // High (Strong in the calc)
    r.getCell(8).value = Math.round(strA);
    r.getCell(8).numFmt = XLSX_STYLES.fmtAdr;
    r.getCell(8).font = XLSX_STYLES.normal10;
    r.getCell(9).value = { formula: `H${rowNum}*C${rowNum}` };
    r.getCell(9).numFmt = XLSX_STYLES.fmtCurrency;
    r.getCell(9).font = XLSX_STYLES.normal10;
  }

  // ---- Row 11: TOTAL ----------------------------------------------------
  const r11 = ws.getRow(11);
  r11.getCell(1).value = "TOTAL";
  r11.getCell(3).value = { formula: "SUM(C5:C10)" };
  r11.getCell(3).numFmt = XLSX_STYLES.fmtNights;
  r11.getCell(5).value = { formula: "SUM(E5:E10)" };
  r11.getCell(5).numFmt = XLSX_STYLES.fmtCurrency;
  r11.getCell(7).value = { formula: "SUM(G5:G10)" };
  r11.getCell(7).numFmt = XLSX_STYLES.fmtCurrency;
  r11.getCell(9).value = { formula: "SUM(I5:I10)" };
  r11.getCell(9).numFmt = XLSX_STYLES.fmtCurrency;
  for (let col = 1; col <= 9; col++) {
    r11.getCell(col).font = XLSX_STYLES.bold10;
    r11.getCell(col).fill = XLSX_STYLES.subtotalBlue;
  }

  // ---- Row 12: '(Occupancy)' helper label -------------------------------
  ws.getCell("B12").value = "(Occupancy) ";
  ws.getCell("B12").font = { size: 11 };

  // ---- Row 13: Management Rate (single source of truth) -----------------
  ws.mergeCells("A13:F13");
  ws.getCell("A13").value = "Management Rate";
  ws.getCell("A13").font = XLSX_STYLES.normal10;
  ws.mergeCells("G13:I13");
  const g13 = ws.getCell("G13");
  g13.value = mgmtRatePct / 100;
  g13.numFmt = XLSX_STYLES.fmtPct1;
  g13.font = XLSX_STYLES.bold11;
  g13.fill = XLSX_STYLES.editableCyan;
  g13.alignment = { horizontal: "center", vertical: "middle" };

  // ---- Row 14: Management rate explainer --------------------------------
  ws.mergeCells("A14:I14");
  const c14 = ws.getCell("A14");
  c14.value = "     ↳ Grand Welcome's management rate as a percentage of rental profit. " +
              "Adjust for this specific home's agreement.";
  c14.font = XLSX_STYLES.italic9;
  c14.alignment = { horizontal: "left", vertical: "middle", wrapText: true };
```

- [ ] **Step 2: Verify the monthly rows + total write correctly**

Open the HTML file. Run a projection (Label=`Test`, Bucket=`3br`, Mid peak=`1000`, others blank). In DevTools console:

```js
const wb = buildWorkbook(lastState, 5500, 16.5, 20);
wb.xlsx.writeBuffer().then(buf => {
  const blob = new Blob([buf]);
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url; a.download = "test1.xlsx";
  document.body.appendChild(a); a.click(); a.remove();
});
```

Open `test1.xlsx` in Excel/Numbers. Verify:
- Row 4 headers read Month · Occ · Nights · Base ADR · Base Revenue · Strong ADR · Strong Revenue · High ADR · High Revenue
- Rows 5–10 have occupancy as percentages, nights as `=31*B5` style formulas, ADRs as raw `$###` numbers, revenues as `=D5*C5` style formulas
- Row 11 shows TOTAL with SUM formulas summing nights + each revenue column
- G13 shows `20.0%` in a cyan-filled cell

- [ ] **Step 3: Commit**

```bash
cd /Users/lucasknowles/gw-revenue-projection
git add project_revenue.html
git commit -m "Write projection table rows 5-11, management rate, row 13-14"
```

---

## Task 7: Implement Pro Forma header + guest payment block (rows 17–24)

**Files:**
- Modify: `project_revenue.html` — extend `buildWorkbook()` with rows 17–24

**Why:** Rows 17–24 are the pro forma intro (title, subtitle, column headers) and the Guest Payment Collected section (nightly fare + turnover collected + total paid).

- [ ] **Step 1: Append rows 17–24 to `buildWorkbook()`**

Insert **before** `return wb;` (after the Task 6 block):

```js
  // ---- Row 17: Pro Forma section title ----------------------------------
  ws.getCell("A17").value = `${titlePhrase} Pro Forma`;
  ws.getCell("A17").font = XLSX_STYLES.bold14;

  // ---- Row 18: Pro Forma subtitle ---------------------------------------
  ws.mergeCells("A18:I18");
  const c18 = ws.getCell("A18");
  c18.value = "How a season's reservations distribute — Base / Strong / High";
  c18.font = { size: 10 };

  // ---- Row 20: Pro Forma column headers ---------------------------------
  const r20 = ws.getRow(20);
  r20.getCell(1).value = "Line Item";
  r20.getCell(1).font = XLSX_STYLES.whiteBold10;
  r20.getCell(1).fill = XLSX_STYLES.headerNavy;
  r20.getCell(1).alignment = { horizontal: "left", vertical: "middle" };
  const proFormaHeads = ["Base", "Strong", "High"];
  proFormaHeads.forEach((h, i) => {
    const cell = r20.getCell(7 + i);
    cell.value = h;
    cell.font = XLSX_STYLES.whiteBold10;
    cell.fill = XLSX_STYLES.headerNavy;
    cell.alignment = { horizontal: "right", vertical: "middle" };
  });

  // ---- Row 21: GUEST PAYMENT COLLECTED (section header) -----------------
  ws.mergeCells("A21:F21");
  const c21 = ws.getCell("A21");
  c21.value = "GUEST PAYMENT COLLECTED";
  c21.font = XLSX_STYLES.bold10;
  c21.fill = XLSX_STYLES.sectionBlue;
  c21.alignment = { horizontal: "left", vertical: "middle" };
  for (let col = 7; col <= 9; col++) {
    ws.getCell(21, col).fill = XLSX_STYLES.sectionBlue;
  }

  // ---- Row 22: Nightly Rental Fare (pulls totals) -----------------------
  ws.mergeCells("A22:F22");
  const c22 = ws.getCell("A22");
  c22.value = "Nightly Rental Fare";
  c22.font = XLSX_STYLES.normal10;
  [["G22", "E11"], ["H22", "G11"], ["I22", "I11"]].forEach(([target, source]) => {
    const cell = ws.getCell(target);
    cell.value = { formula: source };
    cell.numFmt = XLSX_STYLES.fmtCurrency;
    cell.font = XLSX_STYLES.normal10;
  });

  // ---- Row 23: Turnover Charge Collected from Guest ---------------------
  ws.mergeCells("A23:F23");
  const c23 = ws.getCell("A23");
  c23.value = "Turnover Charge Collected from Guest  (approximately 20 guest stays)";
  c23.font = XLSX_STYLES.normal10;
  ["G23", "H23", "I23"].forEach((addr) => {
    const cell = ws.getCell(addr);
    cell.value = Math.round(turnover);
    cell.numFmt = XLSX_STYLES.fmtCurrency;
    cell.font = XLSX_STYLES.normal10;
  });

  // ---- Row 24: Total Paid by Guest --------------------------------------
  ws.mergeCells("A24:F24");
  const c24 = ws.getCell("A24");
  c24.value = "Total Paid by Guest";
  c24.font = XLSX_STYLES.bold10;
  c24.fill = XLSX_STYLES.subtotalBlue;
  [["G24", "G22+G23"], ["H24", "H22+H23"], ["I24", "I22+I23"]].forEach(([addr, f]) => {
    const cell = ws.getCell(addr);
    cell.value = { formula: f };
    cell.numFmt = XLSX_STYLES.fmtCurrency;
    cell.font = XLSX_STYLES.bold10;
    cell.fill = XLSX_STYLES.subtotalBlue;
  });
```

- [ ] **Step 2: Verify**

Re-run the console download snippet from Task 6 Step 2 with a new filename (`test2.xlsx`). Open the file. Verify:
- Row 17: bold "3-Bedroom Pro Forma" title
- Row 18: subtitle "How a season's reservations distribute — Base / Strong / High"
- Row 20: dark navy header row with Line Item · Base · Strong · High
- Row 21: blue band "GUEST PAYMENT COLLECTED"
- Row 22: Nightly Rental Fare with three formulas pulling from E11/G11/I11 (values should equal row 11 totals exactly)
- Row 23: Turnover Charge shows `$5,500` across all three columns
- Row 24: Total Paid by Guest is subtotal-blue and shows the sum of rows 22+23

- [ ] **Step 3: Commit**

```bash
cd /Users/lucasknowles/gw-revenue-projection
git add project_revenue.html
git commit -m "Write Pro Forma header + guest payment block (rows 17-24)"
```

---

## Task 8: Implement operating costs + rental profit (rows 26–33)

**Files:**
- Modify: `project_revenue.html` — extend `buildWorkbook()` with rows 26–33

**Why:** Operating Costs block (Website & Advertising = -Total × bookingFee%, Turnover Costs = -Turnover, Total Op Costs), each with its italicized explainer footnote, then Rental Profit subtotal. Booking fee is baked into the formula as a decimal constant per the spec (e.g. `=-G24*0.165`).

- [ ] **Step 1: Append rows 26–33 to `buildWorkbook()`**

Insert **before** `return wb;` (after the Task 7 block):

```js
  // ---- Row 26: OPERATING COSTS (section header) -------------------------
  ws.mergeCells("A26:F26");
  const c26 = ws.getCell("A26");
  c26.value = "OPERATING COSTS   (Charged to Guests, Paid to Third Parties)";
  c26.font = XLSX_STYLES.bold10;
  c26.fill = XLSX_STYLES.sectionBlue;
  c26.alignment = { horizontal: "left", vertical: "middle" };
  for (let col = 7; col <= 9; col++) {
    ws.getCell(26, col).fill = XLSX_STYLES.sectionBlue;
  }

  // ---- Row 27: Website & Advertising Costs ------------------------------
  const bookingFeeDecimal = (bookingFeePct / 100).toFixed(4).replace(/0+$/, "").replace(/\.$/, "");
  ws.mergeCells("A27:F27");
  const c27 = ws.getCell("A27");
  c27.value = "Website & Advertising Costs";
  c27.font = XLSX_STYLES.normal10;
  [["G27", `-G24*${bookingFeeDecimal}`],
   ["H27", `-H24*${bookingFeeDecimal}`],
   ["I27", `-I24*${bookingFeeDecimal}`]].forEach(([addr, f]) => {
    const cell = ws.getCell(addr);
    cell.value = { formula: f };
    cell.numFmt = XLSX_STYLES.fmtCurrency;
    cell.font = XLSX_STYLES.normal10;
  });

  // ---- Row 28: Explainer footnote (Website/Advertising) -----------------
  ws.mergeCells("A28:I28");
  const c28 = ws.getCell("A28");
  c28.value = "     ↳ Charged by Airbnb, VRBO, and Meta Ads, plus credit card processors. " +
              "A standard cost of booking a vacation rental on any major platform — " +
              "applies to every property listed on these channels, regardless of who manages it.";
  c28.font = XLSX_STYLES.italic9;
  c28.alignment = { horizontal: "left", vertical: "middle", wrapText: true };

  // ---- Row 29: Turnover Costs -------------------------------------------
  ws.mergeCells("A29:F29");
  const c29 = ws.getCell("A29");
  c29.value = "Turnover Costs";
  c29.font = XLSX_STYLES.normal10;
  [["G29", "-G23"], ["H29", "-H23"], ["I29", "-I23"]].forEach(([addr, f]) => {
    const cell = ws.getCell(addr);
    cell.value = { formula: f };
    cell.numFmt = XLSX_STYLES.fmtCurrency;
    cell.font = XLSX_STYLES.normal10;
  });

  // ---- Row 30: Explainer footnote (Turnover) ----------------------------
  ws.mergeCells("A30:I30");
  const c30 = ws.getCell("A30");
  c30.value = "     ↳ Charged by the vendors who service the home between guests — " +
              "cleaners, inspectors, and stocking services. " +
              "A standard cost of any professionally operated vacation rental.";
  c30.font = XLSX_STYLES.italic9;
  c30.alignment = { horizontal: "left", vertical: "middle", wrapText: true };

  // ---- Row 31: Total Operating Costs ------------------------------------
  ws.mergeCells("A31:F31");
  const c31 = ws.getCell("A31");
  c31.value = "Total Operating Costs";
  c31.font = XLSX_STYLES.bold10;
  c31.fill = XLSX_STYLES.subtotalBlue;
  [["G31", "G27+G29"], ["H31", "H27+H29"], ["I31", "I27+I29"]].forEach(([addr, f]) => {
    const cell = ws.getCell(addr);
    cell.value = { formula: f };
    cell.numFmt = XLSX_STYLES.fmtCurrency;
    cell.font = XLSX_STYLES.bold10;
    cell.fill = XLSX_STYLES.subtotalBlue;
  });

  // ---- Row 33: Rental Profit --------------------------------------------
  ws.mergeCells("A33:F33");
  const c33 = ws.getCell("A33");
  c33.value = "Rental Profit   (what remains after the home's operating costs)";
  c33.font = XLSX_STYLES.bold10;
  c33.fill = XLSX_STYLES.subtotalBlue;
  [["G33", "G24+G31"], ["H33", "H24+H31"], ["I33", "I24+I31"]].forEach(([addr, f]) => {
    const cell = ws.getCell(addr);
    cell.value = { formula: f };
    cell.numFmt = XLSX_STYLES.fmtCurrency;
    cell.font = XLSX_STYLES.bold10;
    cell.fill = XLSX_STYLES.subtotalBlue;
  });
```

- [ ] **Step 2: Verify**

Re-download a test .xlsx. Open it. Verify:
- Row 26 blue band "OPERATING COSTS (Charged to Guests, Paid to Third Parties)"
- Row 27 Website & Advertising shows negatives in parentheses (e.g. `($14,500)`) — the booking fee × total paid
- Row 28 italic explainer under the row
- Row 29 Turnover Costs shows `=-G23` etc. (should be `($5,500)` if turnover = 5500)
- Row 31 Total Op Costs is the sum of 27+29
- Row 33 Rental Profit is positive (Total Paid + Total Op Costs where op costs are negative)

Verify numerically: for turnover=5500 and booking=16.5%, row 27 Base col = `-(row24_base)*0.165`. Manually check one value.

- [ ] **Step 3: Commit**

```bash
cd /Users/lucasknowles/gw-revenue-projection
git add project_revenue.html
git commit -m "Write operating costs + rental profit (rows 26-33)"
```

---

## Task 9: Implement management + net + how-to-read (rows 35–43)

**Files:**
- Modify: `project_revenue.html` — extend `buildWorkbook()` with rows 35–43

**Why:** The management section references `$G$13` (set in Task 6) for both the label text and the values, and nets to the green "NET TO HOMEOWNER" row. The how-to-read paragraph uses Base / Strong / High terminology per the rename spec.

- [ ] **Step 1: Append rows 35–43 to `buildWorkbook()`**

Insert **before** `return wb;` (after the Task 8 block):

```js
  // ---- Row 35: GRAND WELCOME MANAGEMENT (section header) ----------------
  ws.mergeCells("A35:F35");
  const c35 = ws.getCell("A35");
  c35.value = "GRAND WELCOME MANAGEMENT";
  c35.font = XLSX_STYLES.bold10;
  c35.fill = XLSX_STYLES.sectionBlue;
  c35.alignment = { horizontal: "left", vertical: "middle" };
  for (let col = 7; col <= 9; col++) {
    ws.getCell(35, col).fill = XLSX_STYLES.sectionBlue;
  }

  // ---- Row 36: Management Rate line (label reads $G$13 via TEXT) --------
  ws.mergeCells("A36:F36");
  const c36 = ws.getCell("A36");
  c36.value = { formula: '"Management Rate  ("&TEXT($G$13,"0%")&" of rental profit)"' };
  c36.font = XLSX_STYLES.normal10;
  [["G36", "-(G33)*$G$13"], ["H36", "-(H33)*$G$13"], ["I36", "-(I33)*$G$13"]].forEach(([addr, f]) => {
    const cell = ws.getCell(addr);
    cell.value = { formula: f };
    cell.numFmt = XLSX_STYLES.fmtCurrency;
    cell.font = XLSX_STYLES.normal10;
  });

  // ---- Row 37: Explainer footnote (management rate) ---------------------
  ws.mergeCells("A37:I37");
  const c37 = ws.getCell("A37");
  c37.value = "     ↳ Like any business, the home covers its operating costs first. " +
              "What remains is rental profit — shared between the homeowner and Grand Welcome " +
              "for managing the property (marketing, booking management, guest communication, " +
              "pricing optimization, owner reporting, 24/7 operational support). " +
              "The majority flows to the homeowner.";
  c37.font = XLSX_STYLES.italic9;
  c37.alignment = { horizontal: "left", vertical: "middle", wrapText: true };

  // ---- Row 39: NET TO HOMEOWNER -----------------------------------------
  ws.mergeCells("A39:F39");
  const c39 = ws.getCell("A39");
  c39.value = "NET TO HOMEOWNER";
  c39.font = XLSX_STYLES.bold11;
  c39.fill = XLSX_STYLES.netGreen;
  c39.alignment = { horizontal: "left", vertical: "middle" };
  [["G39", "G33+G36"], ["H39", "H33+H36"], ["I39", "I33+I36"]].forEach(([addr, f]) => {
    const cell = ws.getCell(addr);
    cell.value = { formula: f };
    cell.numFmt = XLSX_STYLES.fmtCurrency;
    cell.font = XLSX_STYLES.bold11;
    cell.fill = XLSX_STYLES.netGreen;
  });

  // ---- Row 42: HOW TO READ THIS REPORT (section header) -----------------
  ws.mergeCells("A42:I42");
  const c42 = ws.getCell("A42");
  c42.value = "HOW TO READ THIS REPORT";
  c42.font = XLSX_STYLES.bold10;
  c42.fill = XLSX_STYLES.sectionBlue;
  c42.alignment = { horizontal: "left", vertical: "middle" };

  // ---- Row 43: How-to-read body paragraph -------------------------------
  ws.mergeCells("A43:I43");
  const c43 = ws.getCell("A43");
  c43.value =
    "The Base / Strong / High columns represent three realistic seasonal outcomes for this " +
    "home, once the listing is established which is generally year 3+. Strong is our best " +
    "point estimate based on comparable homes in our portfolio and current market demand. " +
    "Base reflects a conservative downside if the nightly rate comes in softer than expected. " +
    "High reflects upside in line with our top comparable properties.\n\n" +
    "Every  vacation rental pays two categories of operating costs: costs charged by the " +
    "booking platforms (Airbnb, VRBO, Meta Ads, card processors) and costs charged by the " +
    "vendors who service the home between guests (cleaners, inspectors, stocking). Both are " +
    "charged directly to guests at the time of booking.\n\n" +
    "What remains is rental profit — shared between the homeowner and Grand Welcome under " +
    "the terms of the management agreement.";
  c43.font = XLSX_STYLES.italic9;
  c43.alignment = { horizontal: "left", vertical: "top", wrapText: true };
  ws.getRow(43).height = 120;
```

- [ ] **Step 2: Verify**

Re-download a test .xlsx. Open it. Verify:
- Row 35 blue band "GRAND WELCOME MANAGEMENT"
- Row 36 label reads `Management Rate  (20% of rental profit)` — the 20% comes from TEXT($G$13,"0%"). Change G13 to 0.25 inside Excel and confirm the label updates to `25%` live.
- Row 36 values are negative (GW's cut, shown as `($X,XXX)`)
- Row 37 italic explainer
- Row 39 NET TO HOMEOWNER is green-filled, bold size 11, and shows Rental Profit + Management (net positive to owner)
- Row 42 blue band "HOW TO READ THIS REPORT"
- Row 43 wraps to multi-paragraph text using Base / Strong / High terminology

- [ ] **Step 3: Commit**

```bash
cd /Users/lucasknowles/gw-revenue-projection
git add project_revenue.html
git commit -m "Write management + net + how-to-read (rows 35-43)

buildWorkbook() is now complete. Downstream task wires the
download handler and the disabled-state logic on the button."
```

---

## Task 10: Wire `downloadExcel()` + disabled-state logic

**Files:**
- Modify: `project_revenue.html` — add `downloadExcel()` function and button wiring near the existing download handlers (around line 779)

**Why:** Connect the button to the workbook builder. Keep the button disabled until both (a) a projection has run and (b) Turnover Charge has a positive numeric value. Disable it again if the user edits the turnover field to blank/invalid.

- [ ] **Step 1: Add the downloadExcel function after buildWorkbook**

Find the end of `buildWorkbook()` (the `return wb;` line added in Task 5 and extended through Task 9). **Immediately after the closing `}` of `buildWorkbook`**, insert:

```js
async function downloadExcel() {
  if (!lastState || !lastState._computed) return;
  if (typeof ExcelJS === "undefined") {
    alert("Excel library failed to load — check your internet connection and refresh.");
    return;
  }
  const turnoverRaw = document.getElementById("turnover_charge").value.trim();
  const turnover = Number(turnoverRaw);
  if (turnoverRaw === "" || !isFinite(turnover) || turnover < 0) {
    alert("Enter a non-negative Turnover Charge to export.");
    return;
  }
  const bookingFeeRaw = document.getElementById("booking_fee_pct").value.trim();
  const bookingFeePct = bookingFeeRaw === "" ? 16.5 : Number(bookingFeeRaw);
  if (!isFinite(bookingFeePct) || bookingFeePct < 0 || bookingFeePct > 100) {
    alert("Booking Fee must be a percentage between 0 and 100.");
    return;
  }
  const mgmtRaw = document.getElementById("mgmt_rate_pct").value.trim();
  const mgmtRatePct = mgmtRaw === "" ? 20.0 : Number(mgmtRaw);
  if (!isFinite(mgmtRatePct) || mgmtRatePct < 0 || mgmtRatePct > 100) {
    alert("Management Rate must be a percentage between 0 and 100.");
    return;
  }

  const wb = buildWorkbook(lastState, turnover, bookingFeePct, mgmtRatePct);
  const buf = await wb.xlsx.writeBuffer();
  const blob = new Blob([buf], {
    type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
  });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `projection_${sanitizeFilename(lastState.label)}_${todayYmd()}.xlsx`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

function refreshExcelButtonState() {
  const btn = document.getElementById("download-xlsx");
  if (!btn) return;
  const turnoverRaw = document.getElementById("turnover_charge").value.trim();
  const turnover = Number(turnoverRaw);
  const turnoverOk = turnoverRaw !== "" && isFinite(turnover) && turnover >= 0;
  const projectionReady = !!(lastState && lastState._computed);
  btn.disabled = !(turnoverOk && projectionReady);
  btn.title = btn.disabled
    ? (projectionReady
        ? "Enter a turnover charge to enable Excel export."
        : "Run a projection first.")
    : "";
}
```

- [ ] **Step 2: Wire the button click + input listener + projection-ready trigger**

Find the bottom of the existing script where other buttons get their listeners (around `project_revenue.html:779-781`). After the existing `document.getElementById("copy-png").addEventListener(...)` line, add:

```js
document.getElementById("download-xlsx").addEventListener("click", downloadExcel);
document.getElementById("turnover_charge").addEventListener("input", refreshExcelButtonState);
```

Then find the `render(state)` function (around line 272). At the end of the function, right before the existing `renderChart(state);` call, add:

```js
  refreshExcelButtonState();
```

So the updated tail of `render()` looks like:

```js
  state._computed = { con, cenS, strS, paragraph: para };

  refreshExcelButtonState();
  renderChart(state);
}
```

Finally, update the form `reset` handler to also refresh the button state. Find `form.addEventListener("reset", ...)` at around line 773. Replace its body with:

```js
form.addEventListener("reset", () => {
  err.textContent = "";
  document.getElementById("output").classList.remove("visible");
  lastState = null;
  refreshExcelButtonState();
});
```

- [ ] **Step 3: Verify end-to-end in a browser**

Open the HTML file. Confirm:
1. On page load, the Download Excel button is disabled.
2. Fill the form (Label=`162 Main Street`, Bucket=`3br`, Use case=`owner_onboarding`, Mid peak=`1000`) → click Project revenue. Button remains disabled (turnover is blank).
3. Type `5500` in Turnover Charge. Button becomes enabled.
4. Clear the turnover field. Button becomes disabled again.
5. Re-enter `5500`, click Download Excel. A file named `projection_162_Main_Street_YYYYMMDD.xlsx` downloads.
6. Open the file. Confirm it matches the reference workbook's layout: title, subtitle, monthly projection table with live formulas, pro forma with guest payment / operating costs / rental profit / management / net to homeowner / how-to-read block.
7. Tweak `G13` from `20%` to `25%` inside Excel. Row 36 label auto-updates to `25% of rental profit` and row 36 values + row 39 NET recalculate.
8. Tweak `B7` (July occupancy) from `92%` to `95%`. Row 11 nights total, row 11 revenue totals, row 22 Nightly Rental Fare, row 24, row 27, row 31, row 33, row 36, row 39 all recalculate.

- [ ] **Step 4: Commit**

```bash
cd /Users/lucasknowles/gw-revenue-projection
git add project_revenue.html
git commit -m "Wire Download Excel button + disabled-state management

Button stays disabled until both a projection has run and
a non-negative Turnover Charge is present. Downloads an
.xlsx file named projection_{label}_{YYYYMMDD}.xlsx."
```

---

## Task 11: End-to-end verification script

**Files:**
- Create: `scripts/verify_xlsx_export.py` (new file; verification only, not shipped with the tool)
- Modify: `.gitignore` — add `scripts/_verify_*.xlsx` to keep generated artifacts out of git

**Why:** Reproducibly compare the exported .xlsx to the reference workbook. This isn't a shipped test suite — it's a one-shot check that can be re-run when the feature changes. Uses Python + Playwright (already used earlier in this project for chart screenshotting) and openpyxl (already installed from reference-parsing work).

- [ ] **Step 1: Add the script**

Create `/Users/lucasknowles/gw-revenue-projection/scripts/verify_xlsx_export.py`:

```python
"""
End-to-end verification of the Excel export in project_revenue.html.

Drives the HTML tool with Playwright, triggers a download, then opens the
resulting .xlsx with openpyxl and checks key cells against the reference
workbook at /Users/lucasknowles/Downloads/Reference Projection Sheet.xlsx.

Run:
  python3 scripts/verify_xlsx_export.py
Requires: playwright (install chromium once: `python3 -m playwright install chromium`)
          openpyxl
"""

import pathlib
import sys
import tempfile

import openpyxl
from playwright.sync_api import sync_playwright

PROJECT = pathlib.Path("/Users/lucasknowles/gw-revenue-projection")
HTML = PROJECT / "project_revenue.html"
REFERENCE = pathlib.Path("/Users/lucasknowles/Downloads/Reference Projection Sheet.xlsx")

# Inputs that match the reference workbook (3-Bedroom, $800/1000/1300 peak ADRs).
FORM_INPUTS = {
    "label": "162 Main Street",
    "bucket": "3br",
    "use_case": "owner_onboarding",
    "peak_central": "1000",
    "peak_conservative": "800",
    "peak_stretch": "1300",
    "turnover_charge": "5500",
    "booking_fee_pct": "16.5",
    "mgmt_rate_pct": "20.0",
}


def fill_and_download(tmp_dir: pathlib.Path) -> pathlib.Path:
    with sync_playwright() as p:
        browser = p.chromium.launch()
        ctx = browser.new_context(accept_downloads=True)
        page = ctx.new_page()
        page.goto(HTML.as_uri(), wait_until="networkidle")

        # Wait for ExcelJS to finish loading.
        page.wait_for_function("typeof ExcelJS === 'object'", timeout=5000)

        # Fill text/number inputs; <select> fields need select_option.
        for field in ("label", "peak_central", "peak_conservative", "peak_stretch",
                      "turnover_charge", "booking_fee_pct", "mgmt_rate_pct"):
            page.fill(f"#{field}", FORM_INPUTS[field])
        page.select_option("#bucket", FORM_INPUTS["bucket"])
        page.select_option("#use_case", FORM_INPUTS["use_case"])

        # Run projection.
        page.click("button[type=submit]")
        page.wait_for_selector("#output.visible")

        # Trigger the download.
        with page.expect_download() as dl_info:
            page.click("#download-xlsx")
        dl = dl_info.value
        out_path = tmp_dir / dl.suggested_filename
        dl.save_as(str(out_path))
        browser.close()
        return out_path


def compare(exported: pathlib.Path) -> list[str]:
    """Compare exported workbook to the reference. Return list of failures."""
    failures: list[str] = []

    ref = openpyxl.load_workbook(REFERENCE, data_only=False)
    got = openpyxl.load_workbook(exported, data_only=False)

    # Sheet names may differ (e.g. '3-Bedroom' both sides) but reference uses '3-Bedroom'.
    if got.sheetnames != ref.sheetnames:
        failures.append(f"Sheet names differ: got {got.sheetnames}, ref {ref.sheetnames}")
        return failures

    ws_ref = ref.active
    ws_got = got.active

    # Check a spot-list of cells that matter: titles, headers, formulas, management rate.
    checks = [
        # (cell, expectation_kind, expected_value_or_formula)
        ("A1", "value_contains", "Revenue Projection"),
        ("A2", "value_contains", "Year 3+ Projection"),
        ("D4", "value_eq", "Base ADR"),
        ("F4", "value_eq", "Strong ADR"),
        ("H4", "value_eq", "High ADR"),
        ("C5", "formula_eq", "=31*B5"),
        ("E7", "formula_eq", "=D7*C7"),
        ("E11", "formula_eq", "=SUM(E5:E10)"),
        ("G13", "value_eq", 0.2),                         # 20%
        ("G22", "formula_eq", "=E11"),
        ("G23", "value_eq", 5500),
        ("G24", "formula_eq", "=G22+G23"),
        ("G27", "formula_eq", "=-G24*0.165"),
        ("G29", "formula_eq", "=-G23"),
        ("G33", "formula_eq", "=G24+G31"),
        ("G36", "formula_eq", "=-(G33)*$G$13"),
        ("G39", "formula_eq", "=G33+G36"),
        ("A20", "value_eq", "Line Item"),
        ("G20", "value_eq", "Base"),
        ("H20", "value_eq", "Strong"),
        ("I20", "value_eq", "High"),
    ]

    for cell_addr, kind, expected in checks:
        actual = ws_got[cell_addr].value
        if kind == "value_eq":
            if actual != expected:
                failures.append(f"{cell_addr}: expected {expected!r}, got {actual!r}")
        elif kind == "value_contains":
            if not (isinstance(actual, str) and expected in actual):
                failures.append(f"{cell_addr}: expected to contain {expected!r}, got {actual!r}")
        elif kind == "formula_eq":
            # openpyxl returns formulas as strings starting with '='.
            if actual != expected:
                failures.append(f"{cell_addr}: expected formula {expected!r}, got {actual!r}")
        else:
            failures.append(f"{cell_addr}: unknown check kind {kind}")

    # Check NET TO HOMEOWNER label cell.
    if ws_got["A39"].value != "NET TO HOMEOWNER":
        failures.append(f"A39: expected 'NET TO HOMEOWNER', got {ws_got['A39'].value!r}")

    # Check fills match on a few landmark cells.
    landmark_fills = [
        ("A4", "FF1F3864"),    # header navy
        ("A21", "FFD9E2F3"),   # section blue
        ("A24", "FFE8EEF7"),   # subtotal
        ("A39", "FFC8E0C8"),   # net green
        ("G13", "FFDAEEF3"),   # editable cyan
    ]
    for cell_addr, want_argb in landmark_fills:
        got_fill = ws_got[cell_addr].fill.fgColor.rgb if ws_got[cell_addr].fill.fgColor else None
        if got_fill != want_argb:
            failures.append(f"{cell_addr} fill: expected {want_argb}, got {got_fill}")

    return failures


def main() -> int:
    if not HTML.exists():
        print(f"HTML not found: {HTML}", file=sys.stderr)
        return 2
    if not REFERENCE.exists():
        print(f"Reference workbook not found: {REFERENCE}", file=sys.stderr)
        return 2

    with tempfile.TemporaryDirectory() as td:
        tmp = pathlib.Path(td)
        print("Driving HTML tool with Playwright…")
        out = fill_and_download(tmp)
        print(f"Downloaded {out.name} ({out.stat().st_size} bytes)")
        failures = compare(out)
        if failures:
            print(f"\n{len(failures)} failure(s):")
            for f in failures:
                print(f"  - {f}")
            return 1
        print("\nAll checks passed.")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 2: Update .gitignore**

Current `.gitignore` (path `/Users/lucasknowles/gw-revenue-projection/.gitignore`) already ignores `projection_*.md` and `chart_*.png`. Append a new line for the exported Excel files so local test artifacts don't leak into git. Edit `.gitignore` and add at the end:

```
projection_*.xlsx
```

- [ ] **Step 3: Run the verification**

```bash
cd /Users/lucasknowles/gw-revenue-projection
python3 scripts/verify_xlsx_export.py
```

Expected output:
```
Driving HTML tool with Playwright…
Downloaded projection_162_Main_Street_YYYYMMDD.xlsx (N bytes)

All checks passed.
```

If any check fails, the script prints the mismatching cell and the expected vs actual value. Fix the `buildWorkbook()` code for that cell, re-run, commit.

- [ ] **Step 4: Commit**

```bash
cd /Users/lucasknowles/gw-revenue-projection
git add scripts/verify_xlsx_export.py .gitignore
git commit -m "Add Playwright+openpyxl verification for .xlsx export

scripts/verify_xlsx_export.py drives the HTML tool, downloads the
exported workbook, and spot-checks formulas, values, fills, and
labels against the reference workbook. Intended for manual re-run
after any change to buildWorkbook() or the surrounding rename logic."
```

---

## Self-Review Summary

Checked against `docs/superpowers/specs/2026-04-20-excel-export-design.md`:

- **Form changes (spec §1):** Tasks 3, 4, 10 cover the three inputs, Download Excel button, defaults, and disabled logic. ✓
- **Rename scope (spec §2):** Task 2 covers preview table headers, chart canvas (subtitle/legend/sidebar/footer), HTML footer note, markdown (labels + headers + disclaimer). Form labels intentionally not touched. ✓
- **Workbook structure (spec §3):** Tasks 5–9 cover every row range: 1–2 (title), 4 (header), 5–10 (months), 11 (total), 12 (helper), 13 (mgmt rate), 14 (footnote), 17–18 (pro forma intro), 20 (pro forma header), 21–24 (guest payment), 26–33 (operating costs, profit), 35–39 (management, net), 42–43 (how-to-read). All fills, number formats, merged cells, and formula addresses match spec §3. ✓
- **Integration (spec §4):** Task 1 adds CDN, Task 10 wires the button + blob download, disabled-state logic + validation. ✓
- **File touch points (spec §5):** All edits are in `project_revenue.html` except the new `scripts/verify_xlsx_export.py` verification artifact. ✓
- **Success criteria (spec):** Task 10 step 3 manually verifies every acceptance criterion. Task 11 automates spot-checks.

No placeholders, no TBDs, no "similar to Task N" references. Each task includes actual code and actual verification commands.

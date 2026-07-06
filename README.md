# GW Revenue Projection Tool

Generates May–October revenue projections for a single Grand Welcome of Southern Coastal Maine home, using the locked v1.0 methodology.

## What it does

Given one to three peak July/August ADR estimates for a home, produces a month-by-month **Soft / Mid / Strong** revenue projection for May through October. The three scenarios reflect market-condition ranges rather than forecasts, and the generated outputs are sized for drop-in use in the Canva revenue sheet.

Output includes a formatted table, the standard Section 7 communication paragraph with totals slotted in, a Canva-sized PNG chart (HTML tool only), and an optional markdown export.

Intended for two internal use cases:

- **Owner onboarding** — setting expectations in sales calls with prospective GW homeowners.
- **Acquisition underwriting** — supporting prospective STR buyers evaluating a home for purchase and GW management. Automatically applies the Section 7 10% haircut to the Conservative scenario.

## How to run

```bash
python3 project_revenue.py
```

Python 3.9+. Standard library only — no `pip install` needed.

You will be prompted for:

1. **Property label** — free text, used only for display and filenames.
2. **Bedroom bucket** — one of `1-2br`, `3br`, `4br`, `5+br`.
3. **Use case** — `owner_onboarding` or `acquisition_underwriting`.
4. **Peak Jul/Aug ADR (Mid)** — required, the midpoint of the market-condition range in dollars.
5. **Peak Jul/Aug ADR (Soft)** — optional, press Enter for 80% of Mid.
6. **Peak Jul/Aug ADR (Strong)** — optional, press Enter for 130% of Mid.

The tool prints the projection to stdout and offers to save the full output as `projection_{label}_{YYYYMMDD}.md` in the current directory.

The HTML tool (`project_revenue.html`) accepts the same inputs in a browser form and produces a print-quality PNG chart sized exactly to the empty rectangle in the Grand Welcome Canva revenue-projection template (7.13″ × 3.38″ @ 300 DPI, = 2139 × 1014 px). Drag the downloaded PNG onto the frame in Canva and it snaps to fit.

## Locked assumptions (v1.0)

These are baked into the tool and match the framework exactly. If any of them do not hold for your home, **adjust the peak ADR input manually** rather than asking for a code change:

- **Full owner availability** across May–October. Owner blocks are not modeled. If the owner intends to block dates, subtract `blocked_nights × projected_ADR_for_that_month` downstream.
- **92% peak Jul/Aug occupancy floor.** Operational assumption for GW-managed homes with full availability, not a market average. No override switch.
- **Town, oceanfront, and property condition not modeled.** Bucket alone drives shape. Account for these via the peak ADR input.
- **v1.1 ratios** (recalibrated 2026-07-06 from Guesty actuals). May/Jun ADR ratios are the mean of realized 2025 and 2026 bucket ratios (measured on owner-released "open" nights only, matching the tool's zero-owner-use design); Sep/Oct are realized 2025 (final-season) ratios; Jul/Aug anchors were validated within 0.04 in both seasons and kept. The OCCUPANCY table was validated against 2026 open-night actuals (May 51% vs 50% assumed, June 74% vs 63%, July 92% vs 92%) and left unchanged. The original v1.0 ratios came from the 2025 qualifying set (13 properties, 3br/5+br blended 50/50 with PriceLabs); the mid-season 2026 benchmark showed those shoulder ratios ran ~2–4 weeks "early" (May priced like mid-June), over-projecting May revenue by ~27% on open nights.
- **Peak ADR input = the expected AVERAGE booked nightly rate across all of July+August combined.** Do not enter a best-week rate — best weeks run ~15% above the two-month blend and will over-project everything.
- **Expected accuracy** (measured, given a correct peak input and full availability): typical home within ±15% for the season, nearly all within ±25%, portfolio aggregate within ~5%. Per-home ±10% is *not* achievable — home idiosyncrasies (min-stays, pets, view, week mix) dominate beyond that.

All four bucket × six month ADR ratios and occupancy values live as constants at the top of `project_revenue.py` (mirrored in `project_revenue.html`). Re-validate every November with `python3 scripts/benchmark_actuals.py --year <season>` and re-blend; a v2.0 framework is planned for the 2027 season.

## Projection log (backend)

Every "Project revenue" run in the HTML tool is saved to a small FastAPI + SQLite service (`app/main.py`) so past projections sent to homeowners can be looked up later — address, all inputs, all three scenarios' monthly numbers, and a snapshot of the exact assumption tables used at the time.

- **Hosted on Railway** (service `gw-revenue-projection`, SQLite on a `/data` volume). The tool is served at the service root `/`; use that URL rather than opening the HTML file locally.
- **Auth:** a single shared password in the `PROJECTIONS_API_KEY` Railway env var (also in `~/.env` as `GW_PROJECTIONS_API_KEY`). The browser asks for it once and stores it in localStorage.
- **History:** the "History" button in the tool lists saved projections (search by address or label) and can reload any record's inputs back into the form.
- **Offline behavior:** if the API is unreachable the run queues in localStorage and flushes on the next page load — the status chip next to the buttons always tells you whether the run was logged.
- API: `POST /api/projections`, `GET /api/projections?q=`, `GET /api/projections/{id}`, `DELETE /api/projections/{id}` (Bearer auth), `GET /healthz`.
- Local dev: `pip install -r requirements-dev.txt && PROJECTIONS_API_KEY=dev uvicorn app.main:app --reload`, tests via `python3 -m pytest tests/ -v`.

## Example

Running against the Framework Section 6 worked example (4BR, Soft $800, Mid $1,000, Strong $1,300) produces:

| Month | Occ | Nights | Soft Rev | Mid Rev | Strong Rev |
|-------|----:|-------:|--------:|--------:|-----------:|
| May   | 50% | 15.5 | $5,332 | $6,665 | $8,664 |
| Jun   | 64% | 19.2 | $10,138 | $12,672 | $16,474 |
| Jul   | 92% | 28.5 | $22,360 | $27,950 | $36,334 |
| Aug   | 92% | 28.5 | $23,272 | $29,090 | $37,818 |
| Sep   | 56% | 16.8 | $8,736 | $10,920 | $14,196 |
| Oct   | 49% | 15.2 | $5,225 | $6,532 | $8,491 |
| **TOTAL** | | | **$75,063** | **$93,829** | **$121,977** |

(v1.1 numbers — the v1.0 tables produced a Mid total of $97,909 for the same inputs; the recalibration trims May/Sep/Oct.) With use case `acquisition_underwriting` and the same peak inputs, the Soft peak is calculated against `$800 × 0.9 = $720`, yielding a proportionally lower Soft total. Mid and Strong are unaffected. The output flags the haircut explicitly.

> Note: internally the framework (PDF v1.0) uses the labels Conservative / Central / Stretch. The tool renames these to Soft / Mid / Strong in all user-facing surfaces (CLI prompts, HTML form, chart, markdown export) to avoid phrasing that reads as a forecast or commitment. Calculation semantics are unchanged.

## Source documents

Methodology and operational rules live in two PDFs (authoritative; this tool is a literal implementation of them):

- **`GW_Revenue_Projection_Framework_v1.pdf`** — the operational spec. Ratios, occupancy, calculation steps, output format, communication template. The tool is the framework.
- **`GW_Revenue_Projection_Methodology_v1.pdf`** — the archaeological record of why the framework exists in this form. Reference only. Do not implement anything from methodology that is not also in the v1.0 framework.

When the v2.0 framework lands after the 2026 season, update `ADR_RATIOS`, `OCCUPANCY`, and the `FRAMEWORK_VERSION` constant in `project_revenue.py` to match.

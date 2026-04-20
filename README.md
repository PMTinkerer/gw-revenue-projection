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
- **v1.0 ratios** derived from 2025 qualifying-set portfolio data (13 properties with 5+ booked nights every May–Oct month). 3br and 5+br buckets are 50/50 blended with PriceLabs market ratios due to small sample size; 1-2br and 4br are 100% portfolio.

All four bucket × six month ADR ratios and occupancy values live as constants at the top of `project_revenue.py` and are pending year-end validation per Framework Section 10. They will be re-derived from combined 2025+2026 data and a v2.0 framework published for the 2027 season.

## Example

Running against the Framework Section 6 worked example (4BR, Soft $800, Mid $1,000, Strong $1,300) produces:

| Month | Occ | Nights | Soft Rev | Mid Rev | Strong Rev |
|-------|----:|-------:|--------:|--------:|-----------:|
| May   | 50% | 15.5 | $6,076 | $7,595 | $9,874 |
| Jun   | 64% | 19.2 | $10,138 | $12,672 | $16,474 |
| Jul   | 92% | 28.5 | $22,360 | $27,950 | $36,334 |
| Aug   | 92% | 28.5 | $23,272 | $29,090 | $37,818 |
| Sep   | 56% | 16.8 | $9,677 | $12,096 | $15,725 |
| Oct   | 49% | 15.2 | $6,805 | $8,506 | $11,058 |
| **TOTAL** | | | **$78,328** | **$97,909** | **$127,282** |

With use case `acquisition_underwriting` and the same peak inputs, the Soft peak is calculated against `$800 × 0.9 = $720`, yielding a Soft total of `$70,495`. Mid and Strong are unaffected. The output flags the haircut explicitly.

> Note: internally the framework (PDF v1.0) uses the labels Conservative / Central / Stretch. The tool renames these to Soft / Mid / Strong in all user-facing surfaces (CLI prompts, HTML form, chart, markdown export) to avoid phrasing that reads as a forecast or commitment. Calculation semantics are unchanged.

## Source documents

Methodology and operational rules live in two PDFs (authoritative; this tool is a literal implementation of them):

- **`GW_Revenue_Projection_Framework_v1.pdf`** — the operational spec. Ratios, occupancy, calculation steps, output format, communication template. The tool is the framework.
- **`GW_Revenue_Projection_Methodology_v1.pdf`** — the archaeological record of why the framework exists in this form. Reference only. Do not implement anything from methodology that is not also in the v1.0 framework.

When the v2.0 framework lands after the 2026 season, update `ADR_RATIOS`, `OCCUPANCY`, and the `FRAMEWORK_VERSION` constant in `project_revenue.py` to match.

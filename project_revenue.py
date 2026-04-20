#!/usr/bin/env python3
"""
Grand Welcome of Southern Coastal Maine — May–October revenue projection tool.

Implements the locked methodology from GW_Revenue_Projection_Framework_v1.0
(April 2026). Produces month-by-month Conservative / Central / Stretch
projections for a single home given peak Jul/Aug ADR estimates.

Single file, standard library only. Python 3.9+.
"""

from __future__ import annotations

import sys
from datetime import date
from typing import Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# v1.0 LOCKED CONSTANTS
# Source: GW_Revenue_Projection_Framework_v1.0 (April 2026), Sections 4 & 5.
# These values will be re-derived and possibly updated after the 2026 season
# per Section 10 (Year-End Validation Plan). Do not edit without bumping to
# v2.0 and refreshing the PDF framework alongside the change.
# ---------------------------------------------------------------------------

FRAMEWORK_VERSION = "1.0"

MONTHS: List[str] = ["May", "Jun", "Jul", "Aug", "Sep", "Oct"]

DAYS_IN_MONTH: Dict[str, int] = {
    "May": 31,
    "Jun": 30,
    "Jul": 31,
    "Aug": 31,
    "Sep": 30,
    "Oct": 31,
}

BUCKETS: List[str] = ["1-2br", "3br", "4br", "5+br"]

# ADR ratios: month ADR = peak Jul/Aug ADR * ratio.
# Framework Section 4. Peak months Jul/Aug are near 1.0 by construction.
ADR_RATIOS: Dict[str, Dict[str, float]] = {
    "1-2br": {"May": 0.64, "Jun": 0.77, "Jul": 1.00, "Aug": 1.00, "Sep": 0.61, "Oct": 0.61},
    "3br":   {"May": 0.64, "Jun": 0.80, "Jul": 1.00, "Aug": 1.00, "Sep": 0.71, "Oct": 0.67},
    "4br":   {"May": 0.49, "Jun": 0.66, "Jul": 0.98, "Aug": 1.02, "Sep": 0.72, "Oct": 0.56},
    "5+br":  {"May": 0.64, "Jun": 0.83, "Jul": 0.99, "Aug": 1.01, "Sep": 0.68, "Oct": 0.59},
}

# Occupancy rates. Jul/Aug are the 92% operational floor (Section 5); the
# other months are PriceLabs bed-segmented 2025 market occupancy.
OCCUPANCY: Dict[str, Dict[str, float]] = {
    "1-2br": {"May": 0.53, "Jun": 0.65, "Jul": 0.92, "Aug": 0.92, "Sep": 0.61, "Oct": 0.62},
    "3br":   {"May": 0.53, "Jun": 0.65, "Jul": 0.92, "Aug": 0.92, "Sep": 0.59, "Oct": 0.57},
    "4br":   {"May": 0.50, "Jun": 0.64, "Jul": 0.92, "Aug": 0.92, "Sep": 0.56, "Oct": 0.49},
    "5+br":  {"May": 0.44, "Jun": 0.58, "Jul": 0.92, "Aug": 0.92, "Sep": 0.48, "Oct": 0.48},
}

USE_CASES = ("owner_onboarding", "acquisition_underwriting")

# Section 7: additional 10% haircut on Conservative when underwriting an
# unmanaged acquisition target.
UNDERWRITING_CONSERVATIVE_HAIRCUT = 0.9

# Section 2 defaults when Conservative/Stretch are not provided.
DEFAULT_CONSERVATIVE_MULT = 0.80
DEFAULT_STRETCH_MULT = 1.30


# ---------------------------------------------------------------------------
# Core calculation
# ---------------------------------------------------------------------------

def project_month(bucket: str, month: str, peak_adr: float) -> Tuple[float, float, float]:
    """Return (adr, nights, revenue) for one month, unrounded."""
    adr = peak_adr * ADR_RATIOS[bucket][month]
    nights = DAYS_IN_MONTH[month] * OCCUPANCY[bucket][month]
    revenue = adr * nights
    return adr, nights, revenue


def project_scenario(bucket: str, peak_adr: float) -> Tuple[List[Dict[str, float]], float]:
    """Return per-month rows (unrounded) and the unrounded total revenue."""
    rows = []
    total = 0.0
    for month in MONTHS:
        adr, nights, revenue = project_month(bucket, month, peak_adr)
        rows.append({
            "month": month,
            "adr": adr,
            "nights": nights,
            "revenue": revenue,
            "occupancy": OCCUPANCY[bucket][month],
        })
        total += revenue
    return rows, total


# ---------------------------------------------------------------------------
# Input prompts
# ---------------------------------------------------------------------------

def prompt_label() -> str:
    while True:
        value = input("Property identifier / label: ").strip()
        if value:
            return value
        print("  Please enter a non-empty label.")


def prompt_bucket() -> str:
    options = ", ".join(BUCKETS)
    while True:
        value = input(f"Bedroom bucket ({options}): ").strip().lower()
        normalized = {b.lower(): b for b in BUCKETS}
        if value in normalized:
            return normalized[value]
        print(f"  Invalid bucket. Must be one of: {options}.")


def prompt_use_case() -> str:
    options = ", ".join(USE_CASES)
    while True:
        value = input(f"Use case ({options}): ").strip().lower()
        if value in USE_CASES:
            return value
        print(f"  Invalid use case. Must be one of: {options}.")


def prompt_positive_float(prompt: str, *, optional: bool = False) -> Optional[float]:
    while True:
        raw = input(prompt).strip()
        if not raw:
            if optional:
                return None
            print("  A value is required.")
            continue
        try:
            value = float(raw.replace("$", "").replace(",", ""))
        except ValueError:
            print("  Please enter a numeric value.")
            continue
        if value <= 0:
            print("  Value must be positive.")
            continue
        return value


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------

def fmt_money(value: float) -> str:
    return f"${round(value):,}"


def fmt_adr(value: float) -> str:
    return f"${round(value):,}"


def fmt_nights(value: float) -> str:
    return f"{value:.1f}"


def fmt_occ(value: float) -> str:
    return f"{round(value * 100)}%"


def sanitize_filename(label: str) -> str:
    # Replace spaces with underscores, strip characters not safe in a
    # filename across macOS/Linux/Windows.
    invalid = set('<>:"/\\|?*\0')
    out = []
    for ch in label:
        if ch == " ":
            out.append("_")
        elif ch in invalid or ord(ch) < 32:
            continue
        else:
            out.append(ch)
    cleaned = "".join(out).strip("._ ")
    return cleaned or "property"


# ---------------------------------------------------------------------------
# Report rendering
# ---------------------------------------------------------------------------

def build_report(
    label: str,
    bucket: str,
    use_case: str,
    peak_conservative_entered: float,
    peak_conservative_used: float,
    peak_central: float,
    peak_stretch: float,
    underwriting_haircut_applied: bool,
) -> Tuple[str, float, float, float]:
    """Build the full human-readable report. Returns (report_text,
    total_conservative, total_central, total_stretch)."""

    con_rows, total_con = project_scenario(bucket, peak_conservative_used)
    cen_rows, total_cen = project_scenario(bucket, peak_central)
    str_rows, total_str = project_scenario(bucket, peak_stretch)

    lines: List[str] = []
    lines.append("=" * 82)
    lines.append("GRAND WELCOME OF SOUTHERN COASTAL MAINE — May–Oct Revenue Projection")
    lines.append(f"Framework v{FRAMEWORK_VERSION}")
    lines.append("=" * 82)
    lines.append(f"Property:   {label}")
    lines.append(f"Bucket:     {bucket}")
    lines.append(f"Use case:   {use_case}")
    lines.append("")
    lines.append("Peak Jul/Aug ADR inputs:")
    if underwriting_haircut_applied:
        lines.append(
            f"  Soft:   {fmt_adr(peak_conservative_entered)} entered "
            f"-> {fmt_adr(peak_conservative_used)} used "
            f"(acquisition_underwriting 10% haircut applied per Section 7)"
        )
    else:
        lines.append(f"  Soft:   {fmt_adr(peak_conservative_used)}")
    lines.append(f"  Mid:    {fmt_adr(peak_central)}")
    lines.append(f"  Strong: {fmt_adr(peak_stretch)}")
    lines.append("")

    # Month-by-month table. Column widths hold "Strong ADR" and "Strong Rev".
    header = (
        f"{'Month':<6}{'Occ':>6}{'Nights':>9}"
        f"{'Soft ADR':>12}{'Soft Rev':>13}"
        f"{'Mid ADR':>12}{'Mid Rev':>13}"
        f"{'Strong ADR':>12}{'Strong Rev':>13}"
    )
    lines.append(header)
    lines.append("-" * len(header))

    for i, month in enumerate(MONTHS):
        c = con_rows[i]
        m = cen_rows[i]
        s = str_rows[i]
        lines.append(
            f"{month:<6}"
            f"{fmt_occ(c['occupancy']):>6}"
            f"{fmt_nights(c['nights']):>9}"
            f"{fmt_adr(c['adr']):>12}"
            f"{fmt_money(c['revenue']):>13}"
            f"{fmt_adr(m['adr']):>12}"
            f"{fmt_money(m['revenue']):>13}"
            f"{fmt_adr(s['adr']):>12}"
            f"{fmt_money(s['revenue']):>13}"
        )

    lines.append("-" * len(header))
    lines.append(
        f"{'TOTAL':<6}{'':>6}{'':>9}"
        f"{'':>12}{fmt_money(total_con):>13}"
        f"{'':>12}{fmt_money(total_cen):>13}"
        f"{'':>12}{fmt_money(total_str):>13}"
    )
    lines.append("")

    # Section 7 communication paragraph.
    lines.append("Standard communication paragraph (Framework Section 7):")
    lines.append("")
    paragraph = (
        f"\"Based on comparable homes in our portfolio and current market demand data, "
        f"and assuming the owner provides full rental availability in peak summer, "
        f"we project {fmt_money(total_cen)} for May through October. "
        f"If the nightly rate comes in softer than expected you're looking at "
        f"{fmt_money(total_con)}; if the home performs like our stronger comps "
        f"you could see {fmt_money(total_str)}. July and August are the most "
        f"predictable months because we consistently fill peak weeks when "
        f"availability is open.\""
    )
    lines.append(paragraph)
    lines.append("")

    return "\n".join(lines), total_con, total_cen, total_str


def save_markdown(
    filepath: str,
    label: str,
    bucket: str,
    use_case: str,
    peak_conservative_entered: float,
    peak_conservative_used: float,
    peak_central: float,
    peak_stretch: float,
    underwriting_haircut_applied: bool,
) -> None:
    con_rows, total_con = project_scenario(bucket, peak_conservative_used)
    cen_rows, total_cen = project_scenario(bucket, peak_central)
    str_rows, total_str = project_scenario(bucket, peak_stretch)

    md: List[str] = []
    md.append(f"# Revenue Projection — {label}")
    md.append("")
    md.append(f"Framework v{FRAMEWORK_VERSION}  ·  Generated {date.today().isoformat()}")
    md.append("")
    md.append(f"- **Property:** {label}")
    md.append(f"- **Bucket:** {bucket}")
    md.append(f"- **Use case:** {use_case}")
    md.append("")
    md.append("## Peak Jul/Aug ADR Inputs")
    md.append("")
    if underwriting_haircut_applied:
        md.append(
            f"- Soft: {fmt_adr(peak_conservative_entered)} entered "
            f"→ **{fmt_adr(peak_conservative_used)} used** "
            f"(acquisition_underwriting 10% haircut applied per Section 7)"
        )
    else:
        md.append(f"- Soft: {fmt_adr(peak_conservative_used)}")
    md.append(f"- Mid: {fmt_adr(peak_central)}")
    md.append(f"- Strong: {fmt_adr(peak_stretch)}")
    md.append("")
    md.append("## Month-by-Month Projection")
    md.append("")
    md.append("| Month | Occ | Nights | Soft ADR | Soft Rev | Mid ADR | Mid Rev | Strong ADR | Strong Rev |")
    md.append("|-------|----:|-------:|---------:|---------:|--------:|--------:|-----------:|-----------:|")
    for i, month in enumerate(MONTHS):
        c = con_rows[i]
        m = cen_rows[i]
        s = str_rows[i]
        md.append(
            f"| {month} | {fmt_occ(c['occupancy'])} | {fmt_nights(c['nights'])} | "
            f"{fmt_adr(c['adr'])} | {fmt_money(c['revenue'])} | "
            f"{fmt_adr(m['adr'])} | {fmt_money(m['revenue'])} | "
            f"{fmt_adr(s['adr'])} | {fmt_money(s['revenue'])} |"
        )
    md.append(
        f"| **TOTAL** | | | | **{fmt_money(total_con)}** | | "
        f"**{fmt_money(total_cen)}** | | **{fmt_money(total_str)}** |"
    )
    md.append("")
    md.append("## Standard Communication (Framework Section 7)")
    md.append("")
    md.append(
        f"> Based on comparable homes in our portfolio and current market demand "
        f"data, and assuming the owner provides full rental availability in peak "
        f"summer, we project {fmt_money(total_cen)} for May through October. "
        f"If the nightly rate comes in softer than expected you're looking at "
        f"{fmt_money(total_con)}; if the home performs like our stronger comps "
        f"you could see {fmt_money(total_str)}. July and August are the most "
        f"predictable months because we consistently fill peak weeks when "
        f"availability is open."
    )
    md.append("")
    md.append("## Context")
    md.append("")
    md.append("- Soft · Mid · Strong reflect market-condition scenarios — not forecasts or commitments.")
    md.append("- Modeled on a mature listing with 3+ years of established reviews.")
    md.append(f"- Framework v{FRAMEWORK_VERSION} (locked ratios; pending year-end validation per Section 10).")
    md.append("")

    with open(filepath, "w", encoding="utf-8") as f:
        f.write("\n".join(md))


# ---------------------------------------------------------------------------
# Interactive flow
# ---------------------------------------------------------------------------

def run_interactive() -> int:
    print("Grand Welcome — May–October Revenue Projection")
    print(f"Framework v{FRAMEWORK_VERSION}\n")

    label = prompt_label()
    bucket = prompt_bucket()
    use_case = prompt_use_case()

    peak_central = prompt_positive_float(
        "Peak Jul/Aug ADR — Mid estimate (required, e.g. 1000): "
    )
    assert peak_central is not None

    peak_conservative_entered = prompt_positive_float(
        f"Peak Jul/Aug ADR — Soft estimate "
        f"(optional, press Enter for 80% of Mid = "
        f"{fmt_adr(peak_central * DEFAULT_CONSERVATIVE_MULT)}): ",
        optional=True,
    )
    if peak_conservative_entered is None:
        peak_conservative_entered = peak_central * DEFAULT_CONSERVATIVE_MULT

    peak_stretch = prompt_positive_float(
        f"Peak Jul/Aug ADR — Strong estimate "
        f"(optional, press Enter for 130% of Mid = "
        f"{fmt_adr(peak_central * DEFAULT_STRETCH_MULT)}): ",
        optional=True,
    )
    if peak_stretch is None:
        peak_stretch = peak_central * DEFAULT_STRETCH_MULT

    underwriting_haircut_applied = use_case == "acquisition_underwriting"
    peak_conservative_used = (
        peak_conservative_entered * UNDERWRITING_CONSERVATIVE_HAIRCUT
        if underwriting_haircut_applied
        else peak_conservative_entered
    )

    print()
    report, _, _, _ = build_report(
        label=label,
        bucket=bucket,
        use_case=use_case,
        peak_conservative_entered=peak_conservative_entered,
        peak_conservative_used=peak_conservative_used,
        peak_central=peak_central,
        peak_stretch=peak_stretch,
        underwriting_haircut_applied=underwriting_haircut_applied,
    )
    print(report)

    answer = input("Save full output to a markdown file? [y/N]: ").strip().lower()
    if answer in ("y", "yes"):
        filename = (
            f"projection_{sanitize_filename(label)}_"
            f"{date.today().strftime('%Y%m%d')}.md"
        )
        save_markdown(
            filepath=filename,
            label=label,
            bucket=bucket,
            use_case=use_case,
            peak_conservative_entered=peak_conservative_entered,
            peak_conservative_used=peak_conservative_used,
            peak_central=peak_central,
            peak_stretch=peak_stretch,
            underwriting_haircut_applied=underwriting_haircut_applied,
        )
        print(f"Saved to {filename}")

    return 0


def main() -> int:
    try:
        return run_interactive()
    except (KeyboardInterrupt, EOFError):
        print("\nCancelled.")
        return 130


if __name__ == "__main__":
    sys.exit(main())

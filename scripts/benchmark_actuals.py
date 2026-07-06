#!/usr/bin/env python3
"""
Season benchmark: validates project_revenue.py's ADR_RATIOS and OCCUPANCY
tables against actual Guesty booking data for a given year.

RUN THIS each November once the season (default May-Oct) is fully in the
books -- after the last checkout and cancellations have settled. Running
mid-season understates occupancy/ADR ratios for months still filling in.
WHAT IT VALIDATES, per bedroom bucket (1-2br/3br/4br/5+br) x month:
  - ADR ratio = month ADR / combined Jul+Aug ADR (mirrors ADR_RATIOS)
  - open-nights occupancy = booked nights / (booked + calendar-available
    nights), clamped to each listing's createdAt to skip pre-onboarding
    days (mirrors OCCUPANCY)
Prints actual vs current side by side, flags |delta| > 0.04, and suggests
a re-blended value (mean of current + actual) for next season.
DATA QUIRKS:
  - Sandpiper by the Sea = 3 Guesty listings (combo + 2 components) with
    cross-blocked calendars -- triple-counts inventory below; flagged at
    runtime, not auto-deduped.
  - active=true listings with isListed=false and fully blocked calendars
    naturally drop out of the open-nights math (near-zero open nights).
USAGE:
    python3 scripts/benchmark_actuals.py --year 2026 [--months 5-10] [--cache-dir .benchmark_cache]
AUTH: scmaine-tokens broker only (get_guesty_token()) -- never per-project
OAuth. Env loaded from ~/.env and ~/proactive-scheduling/.env (never printed).
"""
from __future__ import annotations

import argparse
import calendar
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, timedelta
from typing import Dict, List, Optional, Tuple

# project_revenue.py lives at the repo root, one level up from scripts/.
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)
from project_revenue import ADR_RATIOS, OCCUPANCY  # noqa: E402  current locked tables

BASE = "https://open-api.guesty.com/v1"
BUCKETS = ["1-2br", "3br", "4br", "5+br"]
MONTH_ABBR = {1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "May", 6: "Jun",
              7: "Jul", 8: "Aug", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec"}
SANDPIPER_MARKER = "Sandpiper"
DEVIATION_THRESHOLD = 0.04
LISTING_FIELDS = ("_id nickname title active isListed accommodates bedrooms "
                  "address.city createdAt type tags")
RESERVATION_FIELDS = ("_id listingId status checkIn checkOut checkInDateLocalized "
                      "checkOutDateLocalized source money.fareAccommodation "
                      "money.fareAccommodationAdjusted")

# ---- Env / auth (network-adjacent, guarded imports) ------------------------

def load_env(path: str) -> None:
    """Minimal .env parser; sets os.environ if not already set. Never prints values."""
    if not os.path.exists(path):
        return
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            key, val = key.strip(), val.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = val

def get_token() -> str:
    """Guesty token via the scmaine-tokens broker ONLY -- never a per-project OAuth flow."""
    try:
        from scmaine_tokens import get_guesty_token
    except ImportError as e:
        raise SystemExit(
            "scmaine_tokens is not installed. Install it with:\n"
            "  pip install -e /Users/lucasknowles/scmaine-tokens\n"
            "Do not call Guesty OAuth directly."
        ) from e
    return get_guesty_token()

# ---- Network fetch (sequential; honors Retry-After on 429) -----------------

def http_get(token: str, path: str, params: Optional[dict] = None, max_retries: int = 6) -> dict:
    url = BASE + path
    if params:
        url += "?" + urllib.parse.urlencode(params)
    for attempt in range(max_retries):
        req = urllib.request.Request(url, headers={
            "Authorization": "Bearer " + token, "Accept": "application/json",
        })
        try:
            with urllib.request.urlopen(req, timeout=90) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            if e.code == 429:
                delay = int(e.headers.get("Retry-After") or 5)
                print(f"  429 rate-limited, sleeping {delay}s", flush=True)
                time.sleep(delay + 1)
                continue
            body = e.read().decode()[:300]
            raise RuntimeError(f"HTTP {e.code} on {path}: {body}") from e
        except urllib.error.URLError:
            if attempt < max_retries - 1:
                time.sleep(3 * (attempt + 1))
                continue
            raise
    raise RuntimeError(f"exhausted retries on {path}")

def fetch_listings(token: str) -> List[dict]:
    out, skip = [], 0
    while True:
        data = http_get(token, "/listings", {"fields": LISTING_FIELDS, "limit": 100, "skip": skip})
        batch = data.get("results", [])
        out.extend(batch)
        print(f"  listings: fetched {len(out)}", flush=True)
        if len(batch) < 100:
            break
        skip += 100
        time.sleep(0.3)
    return out

def _keep_overlapping(page: List[dict], lower_bound: date, season_start: date,
                       season_end: date, kept: List[dict]) -> bool:
    """Append season-overlapping reservations from `page` into `kept`.
    Returns True once checkIn drops below lower_bound (rows arrive sorted -checkIn)."""
    for r in page:
        ci = parse_date_safe(r.get("checkInDateLocalized") or (r.get("checkIn") or "")[:10])
        co = parse_date_safe(r.get("checkOutDateLocalized") or (r.get("checkOut") or "")[:10])
        if ci is None:
            continue
        if ci < lower_bound:
            return True
        if ci <= season_end and (co or date.max) >= season_start:
            kept.append(r)
    return False

def fetch_reservations_override(token: str, year: int, months_range: Tuple[int, int]) -> List[dict]:
    """Guesty 'override mode': filters[checkIn][gte] (value ignored server-side)
    returns ALL dates/statuses instead of only upcoming stays. Sort desc by
    checkIn, stop client-side once checkIn drops below Feb 1 of `year`."""
    lower_bound = date(year, 2, 1)
    season_start = date(year, months_range[0], 1)
    season_end = date(year, months_range[1], calendar.monthrange(year, months_range[1])[1])
    kept: List[dict] = []
    skip, page_n = 0, 0
    while True:
        data = http_get(token, "/reservations", {
            "filters[checkIn][gte]": "2020-01-01",
            "sort": "-checkIn", "skip": skip, "limit": 100, "fields": RESERVATION_FIELDS,
        })
        page = data.get("results", [])
        if not page:
            break
        stop = _keep_overlapping(page, lower_bound, season_start, season_end, kept)
        page_n += 1
        skip += 100
        print(f"  reservations page {page_n}: skip={skip} kept={len(kept)}", flush=True)
        if stop or len(page) < 100:
            break
        time.sleep(0.3)
    return kept

def fetch_calendars(token: str, listings: List[dict], start_date: str, end_date: str) -> Dict[str, list]:
    calendars: Dict[str, list] = {}
    active = [l for l in listings if l.get("active")]
    for i, listing in enumerate(active, 1):
        lid = listing["_id"]
        try:
            data = http_get(token, f"/availability-pricing/api/calendar/listings/{lid}",
                             {"startDate": start_date, "endDate": end_date})
            days = data.get("data", {}).get("days", data if isinstance(data, list) else [])
            calendars[lid] = [{"date": d.get("date"), "status": d.get("status")} for d in days]
        except Exception as e:
            calendars[lid] = {"error": str(e)[:200]}
        if i % 10 == 0 or i == len(active):
            print(f"  calendars {i}/{len(active)}", flush=True)
        time.sleep(0.25)
    return calendars

def cached_fetch(cache_dir: str, key: str, fetch_fn) -> object:
    """JSON cache keyed by `key` so re-runs don't re-hit the API."""
    os.makedirs(cache_dir, exist_ok=True)
    path = os.path.join(cache_dir, f"{key}.json")
    if os.path.exists(path):
        print(f"cache hit: {path}", flush=True)
        with open(path) as f:
            return json.load(f)
    result = fetch_fn()
    with open(path, "w") as f:
        json.dump(result, f)
    print(f"cached: {path}", flush=True)
    return result

# ---- Pure compute functions (no network -- unit-testable, importable) ------

def parse_date_safe(s: Optional[str]) -> Optional[date]:
    if not s:
        return None
    try:
        return date(int(s[0:4]), int(s[5:7]), int(s[8:10]))
    except (ValueError, IndexError):
        return None

def bucket_of(bedrooms: Optional[int]) -> Optional[str]:
    if bedrooms is None:
        return None
    if bedrooms <= 2:
        return "1-2br"
    if bedrooms == 3:
        return "3br"
    return "4br" if bedrooms == 4 else "5+br"

def guest_fare(res: dict) -> float:
    money = res.get("money") or {}
    fare = money.get("fareAccommodationAdjusted")
    if fare is None:
        fare = money.get("fareAccommodation")
    return float(fare or 0)

def is_guest_reservation(res: dict) -> bool:
    """Guest (revenue) reservation: confirmed, non-owner source, positive fare."""
    if (res.get("status") or "") != "confirmed":
        return False
    if res.get("source") in ("owner", "owner-guest"):
        return False
    return guest_fare(res) > 0

def allocate_nights(check_in: date, check_out: date, fare: float, year: int) -> Dict[str, Tuple[int, float]]:
    """Split `fare` evenly across every night of [check_in, check_out) and
    allocate to the calendar month each night falls in (within `year`).
    Returns {month_abbr: (nights, fare)}."""
    total_nights = (check_out - check_in).days
    if total_nights <= 0:
        return {}
    nightly = fare / total_nights
    out: Dict[str, Tuple[int, float]] = {}
    d = check_in
    while d < check_out:
        if d.year == year:
            mon = MONTH_ABBR[d.month]
            n, f = out.get(mon, (0, 0.0))
            out[mon] = (n + 1, f + nightly)
        d += timedelta(days=1)
    return out

def aggregate_reservation_nights(reservations: List[dict], listings_index: Dict[str, dict],
                                  year: int, months: List[str]) -> Dict[Tuple[str, str], Dict[str, float]]:
    """Per (listing_id, month): guest-booked nights + allocated fare."""
    per: Dict[Tuple[str, str], Dict[str, float]] = {}
    for r in reservations:
        if not is_guest_reservation(r):
            continue
        lid = r.get("listingId")
        entry = listings_index.get(lid)
        if not entry or not entry.get("bucket"):
            continue
        ci = parse_date_safe(r.get("checkInDateLocalized") or (r.get("checkIn") or "")[:10])
        co = parse_date_safe(r.get("checkOutDateLocalized") or (r.get("checkOut") or "")[:10])
        if not ci or not co:
            continue
        for month, (n, f) in allocate_nights(ci, co, guest_fare(r), year).items():
            if month not in months:
                continue
            c = per.setdefault((lid, month), {"nights": 0, "fare": 0.0})
            c["nights"] += n
            c["fare"] += f
    return per

def available_days_by_month(calendar_days: List[dict], created_at: Optional[str], year: int) -> Dict[str, int]:
    """Count calendar 'available' days per month, skipping any day before
    the listing's createdAt (pre-onboarding days don't count either way)."""
    created = parse_date_safe(created_at[:10]) if created_at else None
    out: Dict[str, int] = {}
    for d in calendar_days:
        day = parse_date_safe(d.get("date")) if isinstance(d, dict) else None
        if day is None or day.year != year:
            continue
        if created and day < created:
            continue
        if d.get("status") == "available":
            mon = MONTH_ABBR[day.month]
            out[mon] = out.get(mon, 0) + 1
    return out

def open_nights_occupancy(booked_nights: float, available_days: float) -> Optional[float]:
    open_nights = booked_nights + available_days
    return booked_nights / open_nights if open_nights > 0 else None

def bucket_month_actuals(per_lid_month: Dict[Tuple[str, str], Dict[str, float]],
                          avail_by_lid_month: Dict[Tuple[str, str], int],
                          listings_index: Dict[str, dict], months: List[str]) -> Dict[str, Dict[str, dict]]:
    """Roll per-listing (nights, fare, avail) up to per-bucket per-month {nights, fare, avail, adr, occ}."""
    out = {b: {m: {"nights": 0, "fare": 0.0, "avail": 0} for m in months} for b in BUCKETS}
    for (lid, m), agg in per_lid_month.items():
        b = listings_index.get(lid, {}).get("bucket")
        if b not in out or m not in out[b]:
            continue
        out[b][m]["nights"] += agg["nights"]
        out[b][m]["fare"] += agg["fare"]
    for (lid, m), avail in avail_by_lid_month.items():
        b = listings_index.get(lid, {}).get("bucket")
        if b not in out or m not in out[b]:
            continue
        out[b][m]["avail"] += avail
    for b in BUCKETS:
        for m in months:
            c = out[b][m]
            c["adr"] = c["fare"] / c["nights"] if c["nights"] else None
            c["occ"] = open_nights_occupancy(c["nights"], c["avail"])
    return out

def bucket_adr_ratios(bucket_actuals: Dict[str, Dict[str, dict]]) -> Dict[str, Dict[str, Optional[float]]]:
    """ratio = month ADR / combined Jul+Aug ADR, per bucket."""
    out: Dict[str, Dict[str, Optional[float]]] = {}
    for b, months_data in bucket_actuals.items():
        jul = months_data.get("Jul", {"nights": 0, "fare": 0.0})
        aug = months_data.get("Aug", {"nights": 0, "fare": 0.0})
        peak_nights = jul.get("nights", 0) + aug.get("nights", 0)
        peak_fare = jul.get("fare", 0.0) + aug.get("fare", 0.0)
        peak_adr = peak_fare / peak_nights if peak_nights else None
        ratios: Dict[str, Optional[float]] = {}
        for m, c in months_data.items():
            ratios[m] = round(c["adr"] / peak_adr, 3) if c.get("adr") and peak_adr else None
        out[b] = ratios
    return out

def compare_tables(actual: Dict[str, Dict[str, Optional[float]]], current: Dict[str, Dict[str, float]],
                    threshold: float = DEVIATION_THRESHOLD) -> List[dict]:
    """Compare actual vs current per bucket/month; flag |delta| > threshold,
    suggest a re-blended value (mean of current + actual)."""
    rows = []
    for b in BUCKETS:
        for m, cur_val in current.get(b, {}).items():
            act_val = actual.get(b, {}).get(m)
            if act_val is None:
                continue
            delta = act_val - cur_val
            rows.append({
                "bucket": b, "month": m, "current": cur_val, "actual": act_val,
                "delta": round(delta, 3), "flag": abs(delta) > threshold,
                "suggested": round((cur_val + act_val) / 2, 3),
            })
    return rows

# ---- CLI orchestration ------------------------------------------------------

def parse_months_arg(s: str) -> Tuple[int, int]:
    lo, _, hi = s.partition("-")
    return int(lo), int(hi)

def build_listings_index(listings: List[dict]) -> Dict[str, dict]:
    idx = {}
    for l in listings:
        idx[l["_id"]] = {
            "name": l.get("nickname") or l.get("title") or l["_id"],
            "bucket": bucket_of(l.get("bedrooms")),
            "active": bool(l.get("active")),
            "created": (l.get("createdAt") or "")[:10],
        }
    return idx

def print_sandpiper_warning(listings_index: Dict[str, dict]) -> None:
    matches = [e["name"] for e in listings_index.values() if SANDPIPER_MARKER in (e.get("name") or "")]
    if matches:
        print(f"\nWARNING: Sandpiper by the Sea is modeled as {len(matches)} Guesty listings "
              f"with cross-blocked calendars: {matches}. Inventory counts below "
              "TRIPLE-COUNT this property -- known quirk, not a bug.\n", flush=True)

def print_comparison_table(label: str, rows: List[dict]) -> None:
    print(f"\n{label} -- current vs actual (flag if |delta| > {DEVIATION_THRESHOLD}):")
    print(f"{'bucket':<7}{'month':<5}{'current':>9}{'actual':>9}{'delta':>8}{'flag':>5}{'suggested':>11}")
    for r in rows:
        flag = "**" if r["flag"] else ""
        print(f"{r['bucket']:<7}{r['month']:<5}{r['current']:>9.3f}{r['actual']:>9.3f}"
              f"{r['delta']:>+8.3f}{flag:>5}{r['suggested']:>11.3f}")

def fetch_all(token: str, year: int, months_range: Tuple[int, int], cache_dir: str
              ) -> Tuple[List[dict], List[dict], Dict[str, list]]:
    listings = cached_fetch(cache_dir, f"listings_{year}", lambda: fetch_listings(token))
    reservations = cached_fetch(
        cache_dir, f"reservations_{year}_{months_range[0]}-{months_range[1]}",
        lambda: fetch_reservations_override(token, year, months_range))
    season_start = f"{year}-{months_range[0]:02d}-01"
    end_day = calendar.monthrange(year, months_range[1])[1]
    season_end = f"{year}-{months_range[1]:02d}-{end_day:02d}"
    calendars = cached_fetch(
        cache_dir, f"calendars_{year}_{months_range[0]}-{months_range[1]}",
        lambda: fetch_calendars(token, listings, season_start, season_end))
    return listings, reservations, calendars

def compute_actuals(listings: List[dict], reservations: List[dict], calendars: Dict[str, list],
                     year: int, months: List[str]) -> Tuple[Dict[str, dict], Dict, Dict]:
    listings_index = build_listings_index(listings)
    per_lid_month = aggregate_reservation_nights(reservations, listings_index, year, months)
    avail_by_lid_month: Dict[Tuple[str, str], int] = {}
    for lid, days in calendars.items():
        if not isinstance(days, list):
            continue
        created = listings_index.get(lid, {}).get("created")
        for m, cnt in available_days_by_month(days, created, year).items():
            avail_by_lid_month[(lid, m)] = cnt
    bucket_actuals = bucket_month_actuals(per_lid_month, avail_by_lid_month, listings_index, months)
    actual_ratios = bucket_adr_ratios(bucket_actuals)
    actual_occ = {b: {m: c["occ"] for m, c in md.items()} for b, md in bucket_actuals.items()}
    return listings_index, actual_ratios, actual_occ

def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                      formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--year", type=int, required=True, help="season year, e.g. 2026")
    parser.add_argument("--months", default="5-10", help="month range, e.g. 5-10 (default May-Oct)")
    parser.add_argument("--cache-dir", default=".benchmark_cache", help="on-disk JSON cache dir")
    args = parser.parse_args(argv)
    months_range = parse_months_arg(args.months)
    months = [MONTH_ABBR[m] for m in range(months_range[0], months_range[1] + 1)]
    load_env(os.path.expanduser("~/.env"))
    load_env(os.path.expanduser("~/proactive-scheduling/.env"))
    token = get_token()
    listings, reservations, calendars = fetch_all(token, args.year, months_range, args.cache_dir)
    listings_index, actual_ratios, actual_occ = compute_actuals(
        listings, reservations, calendars, args.year, months)
    print_sandpiper_warning(listings_index)
    print_comparison_table("ADR RATIO", compare_tables(actual_ratios, ADR_RATIOS))
    print_comparison_table("OCCUPANCY", compare_tables(actual_occ, OCCUPANCY))
    return 0

if __name__ == "__main__":
    sys.exit(main())

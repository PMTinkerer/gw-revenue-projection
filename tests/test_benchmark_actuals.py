"""Happy-path tests for the pure compute functions in benchmark_actuals.py.

No network involved -- these exercise allocate_nights (month-boundary
splitting), the bucket ADR-ratio pipeline, and open-nights occupancy with
createdAt clamping, using small fixture dicts shaped like Guesty API output.
"""
import os
import sys
from datetime import date

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import benchmark_actuals as ba  # noqa: E402


# ---- allocate_nights: month-boundary split ---------------------------------

def test_allocate_nights_splits_evenly_across_month_boundary():
    # 4-night stay, Apr 29 -> May 3: 2 nights in Apr, 2 nights in May.
    result = ba.allocate_nights(date(2026, 4, 29), date(2026, 5, 3), fare=400.0, year=2026)
    assert result["Apr"] == (2, 200.0)
    assert result["May"] == (2, 200.0)
    assert set(result) == {"Apr", "May"}


def test_allocate_nights_zero_or_negative_stay_returns_empty():
    assert ba.allocate_nights(date(2026, 5, 5), date(2026, 5, 5), fare=100.0, year=2026) == {}


def test_allocate_nights_filters_to_requested_year():
    # 3-night stay Dec 30 -> Jan 2: nights are Dec30, Dec31, Jan1 (checkout
    # exclusive). Only the single Jan1 night falls in year=2026.
    result = ba.allocate_nights(date(2025, 12, 30), date(2026, 1, 2), fare=300.0, year=2026)
    assert result["Jan"] == (1, 100.0)
    assert "Dec" not in result


# ---- bucket ratio computation ----------------------------------------------

def test_bucket_adr_ratios_computes_ratio_to_combined_peak():
    bucket_actuals = {
        "3br": {
            "May": {"nights": 10, "fare": 5000.0, "avail": 0, "adr": 500.0, "occ": None},
            "Jul": {"nights": 20, "fare": 20000.0, "avail": 0, "adr": 1000.0, "occ": None},
            "Aug": {"nights": 20, "fare": 20000.0, "avail": 0, "adr": 1000.0, "occ": None},
        },
    }
    ratios = ba.bucket_adr_ratios(bucket_actuals)
    # peak adr = (20000+20000)/(20+20) = 1000; May ratio = 500/1000 = 0.5
    assert ratios["3br"]["May"] == 0.5
    assert ratios["3br"]["Jul"] == 1.0
    assert ratios["3br"]["Aug"] == 1.0


def test_bucket_adr_ratios_none_when_no_peak_nights():
    bucket_actuals = {"4br": {"May": {"nights": 5, "fare": 1000.0, "avail": 0, "adr": 200.0, "occ": None}}}
    ratios = ba.bucket_adr_ratios(bucket_actuals)
    assert ratios["4br"]["May"] is None


def test_compare_tables_flags_deviation_and_suggests_reblend():
    actual = {"3br": {"May": 0.70}}
    current = {"3br": {"May": 0.64}}
    rows = ba.compare_tables(actual, current, threshold=0.04)
    row = rows[0]
    assert row["delta"] == 0.06
    assert row["flag"] is True
    assert row["suggested"] == 0.67


# ---- open-nights occupancy with createdAt clamping -------------------------

def test_available_days_by_month_skips_days_before_created_at():
    calendar_days = [
        {"date": "2026-05-01", "status": "available"},  # before onboarding -> skipped
        {"date": "2026-05-10", "status": "available"},  # after onboarding -> counted
        {"date": "2026-05-11", "status": "booked"},      # not 'available' -> not counted
    ]
    result = ba.available_days_by_month(calendar_days, created_at="2026-05-05", year=2026)
    assert result == {"May": 1}


def test_available_days_by_month_no_created_at_counts_all_available():
    calendar_days = [
        {"date": "2026-06-01", "status": "available"},
        {"date": "2026-06-02", "status": "available"},
    ]
    result = ba.available_days_by_month(calendar_days, created_at=None, year=2026)
    assert result == {"Jun": 2}


def test_open_nights_occupancy_basic_ratio():
    # 15 booked nights + 5 available (open) nights -> 15/20 = 0.75
    assert ba.open_nights_occupancy(15, 5) == 0.75


def test_open_nights_occupancy_none_when_no_open_nights():
    assert ba.open_nights_occupancy(0, 0) is None


def test_bucket_month_actuals_combines_nights_fare_and_clamped_avail():
    per_lid_month = {
        ("lid-1", "May"): {"nights": 10, "fare": 5000.0},
    }
    avail_by_lid_month = {("lid-1", "May"): 10}
    listings_index = {"lid-1": {"bucket": "3br"}}
    out = ba.bucket_month_actuals(per_lid_month, avail_by_lid_month, listings_index, ["May"])
    cell = out["3br"]["May"]
    assert cell["nights"] == 10
    assert cell["adr"] == 500.0
    assert cell["occ"] == 0.5  # 10 booked / (10 booked + 10 available)


# ---- reservation classification --------------------------------------------

def test_is_guest_reservation_excludes_owner_blocks_and_zero_fare():
    guest = {"status": "confirmed", "source": "airbnb",
              "money": {"fareAccommodationAdjusted": 500.0}}
    owner_block = {"status": "confirmed", "source": "owner",
                    "money": {"fareAccommodationAdjusted": 0}}
    zero_fare = {"status": "confirmed", "source": "airbnb",
                  "money": {"fareAccommodationAdjusted": 0}}
    not_confirmed = {"status": "canceled", "source": "airbnb",
                       "money": {"fareAccommodationAdjusted": 500.0}}
    assert ba.is_guest_reservation(guest) is True
    assert ba.is_guest_reservation(owner_block) is False
    assert ba.is_guest_reservation(zero_fare) is False
    assert ba.is_guest_reservation(not_confirmed) is False


def test_guest_fare_falls_back_to_unadjusted_when_adjusted_missing():
    res = {"money": {"fareAccommodation": 750.0}}
    assert ba.guest_fare(res) == 750.0


def test_bucket_of_maps_bedrooms_to_expected_buckets():
    assert ba.bucket_of(1) == "1-2br"
    assert ba.bucket_of(2) == "1-2br"
    assert ba.bucket_of(3) == "3br"
    assert ba.bucket_of(4) == "4br"
    assert ba.bucket_of(6) == "5+br"
    assert ba.bucket_of(None) is None

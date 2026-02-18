from pathlib import Path

from leadgen.paths import build_pack_paths, slugify


def test_slugify_basic_cases():
    assert slugify("Boca Raton, FL") == "boca_raton_fl"
    assert slugify("Palm Beach County") == "palm_beach_county"
    assert slugify("Tour Companies & Excursion Operators") == "tour_companies_excursion_operators"


def test_build_pack_paths_full_hierarchy():
    base = Path("data/packs")
    csv_path, jsonl_path = build_pack_paths(
        base_dir=base,
        country="usa",
        state="florida",
        county="palm beach county",
        city="boca raton",
        niche="restaurants",
        default_basename="restaurants_boca_raton_fl",
    )
    expected_dir = base / "usa" / "florida" / "palm_beach_county" / "boca_raton" / "restaurants"
    assert csv_path == expected_dir / "restaurants_boca_raton_fl.csv"
    assert jsonl_path == expected_dir / "restaurants_boca_raton_fl.jsonl"


def test_build_pack_paths_missing_optional_components():
    base = Path("data/packs")
    csv_path, jsonl_path = build_pack_paths(
        base_dir=base,
        country="jamaica",
        state=None,
        county=None,
        city="kingston",
        niche=None,
        default_basename="tour_companies",
    )
    expected_dir = base / "jamaica" / "kingston"
    assert csv_path == expected_dir / "tour_companies.csv"
    assert jsonl_path == expected_dir / "tour_companies.jsonl"

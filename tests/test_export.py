import csv
from pathlib import Path

import pytest

from leadgen.export import export_csv
from leadgen.models import Business, WebsiteAnalysis, LeadResult


EXPECTED_HEADERS = [
    "name",
    "address",
    "website",
    "phone",
    "email",
    "needs_website",
    "needs_redesign",
    "needs_chatbot",
    "needs_ai_integration",
    "score",
    "recommended_services",
    "outreach_message",
    "enriched_title",
    "verified_email_status",
    "apollo_company",
]


def _make_sample_lead(
    name="Test Biz",
    address="123 Main St",
    website="https://example.com",
    phone="555-1234",
    email="test@example.com",
    needs_website=False,
    needs_redesign=True,
    needs_chatbot=True,
    needs_ai_integration=True,
) -> LeadResult:
    """Helper to construct a sample LeadResult."""
    business = Business(
        name=name,
        address=address,
        website=website,
        phone=phone,
        email=email,
        place_id="some-place-id",
    )
    analysis = WebsiteAnalysis(
        has_website=not needs_website,
        needs_website=needs_website,
        needs_redesign=needs_redesign,
        needs_chatbot=needs_chatbot,
        needs_ai_integration=needs_ai_integration,
        raw_data={},
    )
    return LeadResult(business=business, analysis=analysis)


def test_export_csv_writes_correct_headers_and_single_row(tmp_path: Path):
    """export_csv should create a CSV with expected headers and one row."""
    output_file = tmp_path / "leads.csv"
    lead = _make_sample_lead(
        name="Cool Pizza",
        address="42 Slice Ave",
        website="https://pizza.cool",
        phone="512-555-0000",
        email="contact@pizza.cool",
        needs_website=False,
        needs_redesign=True,
        needs_chatbot=True,
        needs_ai_integration=True,
    )

    export_csv([lead], output=str(output_file))

    assert output_file.exists(), "CSV file was not created"

    with output_file.open(newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        rows = list(reader)

    # First row = headers
    assert rows[0] == EXPECTED_HEADERS

    # Second row = data
    data_row = rows[1]
    assert data_row[0] == "Cool Pizza"
    assert data_row[1] == "42 Slice Ave"
    assert data_row[2] == "https://pizza.cool"
    assert data_row[3] == "512-555-0000"
    assert data_row[4] == "contact@pizza.cool"
    # The boolean fields should be written as 'True'/'False' strings by DictWriter
    assert data_row[5] == "False"  # needs_website
    assert data_row[6] == "True"   # needs_redesign
    assert data_row[7] == "True"   # needs_chatbot
    assert data_row[8] == "True"   # needs_ai_integration
    # Score/recommended services populated by ai_scoring helpers
    assert data_row[9].isdigit()
    assert "Website redesign" in data_row[10]
    assert "Hi" in data_row[11]
    # Enrichment columns should exist (may be empty)
    assert len(data_row) == len(EXPECTED_HEADERS)


def test_export_csv_handles_empty_results_creates_headers_only(tmp_path: Path):
    """
    export_csv([]) should not crash.

    Expected behavior for this project:
    - create the file
    - write only the header row (no data rows)
    """
    output_file = tmp_path / "leads_empty.csv"

    # This will currently fail with IndexError if export_csv assumes rows[0].
    # TDD: adjust implementation so it uses known headers when results are empty.
    export_csv([], output=str(output_file))

    assert output_file.exists(), "CSV file was not created for empty results"

    with output_file.open(newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        rows = list(reader)

    # Exactly one row: the header
    assert len(rows) == 1
    assert rows[0] == EXPECTED_HEADERS


def test_export_csv_handles_special_characters_in_fields(tmp_path: Path):
    """Fields with commas/quotes should be correctly CSV-escaped."""
    output_file = tmp_path / "leads_special.csv"

    lead = _make_sample_lead(
        name='Cool "Pizza", Inc.',
        address="123, Sauce Street",
        website="https://example.com/menu?item=pizza&size=large",
        phone="+1-800-555-7777",
        email="sales@example.com",
    )

    export_csv([lead], output=str(output_file))

    with output_file.open(newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        rows = list(reader)

    assert rows[0] == EXPECTED_HEADERS
    data_row = rows[1]
    # DictWriter + csv.reader round-trip should preserve field values
    assert data_row[0] == 'Cool "Pizza", Inc.'
    assert data_row[1] == "123, Sauce Street"
    assert data_row[2] == "https://example.com/menu?item=pizza&size=large"
    assert data_row[3] == "+1-800-555-7777"
    assert data_row[4] == "sales@example.com"
    assert len(data_row) == len(EXPECTED_HEADERS)


def test_export_csv_includes_enriched_headers_when_needed(tmp_path: Path):
    enriched_headers = [
        "tech_stack",
        "enrichment_used",
        "scrape_source",
        "email_confidence",
        "hunter_domain_status",
        "hunter_suggested_emails",
        "org_name",
        "org_website",
        "org_linkedin_url",
        "org_industry",
        "org_employee_count",
        "org_annual_revenue",
        "org_location",
        "org_is_hiring",
        "org_job_postings_count",
    ]
    output_file = tmp_path / "enriched.csv"
    lead = _make_sample_lead()
    lead.tech_stack = {"tech": ["A", "B"]}
    lead.enrichment_used = "enriched"
    lead.org_name = "Org Inc"
    export_csv([lead], output=str(output_file))
    with output_file.open(newline="", encoding="utf-8") as f:
        headers = next(csv.reader(f))
    assert headers[: len(EXPECTED_HEADERS)] == EXPECTED_HEADERS
    assert headers[-len(enriched_headers) :] == enriched_headers


def test_export_csv_raises_for_unwritable_path(tmp_path: Path):
    """
    If the output path is unwritable/non-existent, export_csv should surface the error.

    Here we pass a file path in a directory that does not exist; open() should raise
    FileNotFoundError or OSError. We assert that export_csv does not swallow it.
    """
    non_existent_dir = tmp_path / "does_not_exist"
    output_file = non_existent_dir / "leads.csv"

    with pytest.raises((FileNotFoundError, OSError)):
        export_csv([], output=str(output_file))

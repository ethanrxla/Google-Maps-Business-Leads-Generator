import json
from pathlib import Path

from leadgen.export import export_jsonl
from leadgen.models import Business, LeadResult, WebsiteAnalysis


def _lead(name: str) -> LeadResult:
    business = Business(
        name=name,
        address="123 St",
        website="https://example.com",
        phone="555-0000",
        email="info@example.com",
        place_id="pid",
    )
    analysis = WebsiteAnalysis(
        has_website=True,
        needs_website=False,
        needs_redesign=True,
        needs_chatbot=True,
        needs_ai_integration=True,
        raw_data={},
    )
    return LeadResult(business=business, analysis=analysis)


def test_export_jsonl_writes_lines(tmp_path: Path):
    output = tmp_path / "leads.jsonl"
    leads = [_lead("Biz1"), _lead("Biz2")]

    export_jsonl(leads, str(output))

    assert output.exists()
    with output.open() as f:
        lines = [json.loads(line) for line in f.readlines()]

    assert len(lines) == 2
    assert lines[0]["name"] == "Biz1"
    assert isinstance(lines[0]["recommended_services"], list)
    assert "outreach_message" in lines[0]
    assert lines[0].get("email_source") is None

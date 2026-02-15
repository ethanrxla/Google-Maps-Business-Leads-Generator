import json

from leadgen.generator import generate_pack
from leadgen.models import Business, WebsiteAnalysis


class DummyAnalysis(WebsiteAnalysis):
    def __init__(self, *, has_website: bool = True):
        super().__init__(
            has_website=has_website,
            needs_website=not has_website,
            needs_redesign=True,
            needs_chatbot=True,
            needs_ai_integration=True,
            raw_data={},
        )


def _lead(name: str, website: str | None, phone: str | None, email: str | None):
    return Business(name=name, address="Addr", website=website, phone=phone, email=email, place_id=None)


def _patch_pipeline(monkeypatch, analysis: DummyAnalysis):
    monkeypatch.setattr("leadgen.generator.get_details", lambda b: b)
    monkeypatch.setattr("leadgen.generator.fetch_html", lambda url: "<html></html>")
    monkeypatch.setattr("leadgen.generator.extract_emails", lambda html: [])
    monkeypatch.setattr("leadgen.generator.apply_email_patterns", lambda b: None)
    monkeypatch.setattr("leadgen.generator.analyze_html", lambda html: analysis)
    monkeypatch.setattr("leadgen.generator.export_csv", lambda leads, output: None)
    monkeypatch.setattr("leadgen.generator.export_jsonl", lambda leads, output: None)


def test_generate_pack_sets_sellable_false_and_emits_failure_reasons(monkeypatch, tmp_path):
    _patch_pipeline(monkeypatch, DummyAnalysis(has_website=False))

    # Intentionally fail multiple gates: no phone/email/website and low score.
    businesses = [
        _lead(name=f"Biz {i}", website=None, phone=None, email=None)
        for i in range(5)
    ]

    summary = generate_pack(
        query="q",
        country="usa",
        state="fl",
        county=None,
        city="city",
        niche="niche",
        limit=10,
        pack_id="pid-unsellable",
        base_dir=tmp_path,
        output_csv=tmp_path / "out.csv",
        output_jsonl=tmp_path / "out.jsonl",
        businesses=businesses,
        status="OK",
        enrichment_tier="basic",
    )

    assert summary["sellable"] is False
    assert summary["quality_gate_failures"]
    assert any("email_coverage" in r for r in summary["quality_gate_failures"])

    summary_path = summary["summary_path"]
    assert summary_path.exists()

    artifact = json.loads(summary_path.read_text())
    assert artifact["sellable"] is False
    assert artifact["quality_gate_failures"] == summary["quality_gate_failures"]


def test_generate_pack_sets_sellable_true_when_gates_pass(monkeypatch, tmp_path):
    _patch_pipeline(monkeypatch, DummyAnalysis(has_website=True))

    businesses = [
        _lead(
            name=f"Biz {i}",
            website=f"https://biz{i}.example.com",
            phone="(555) 123-4567",
            email=f"hello{i}@bizmail.co",
        )
        for i in range(10)
    ]

    summary = generate_pack(
        query="q",
        country="usa",
        state="fl",
        county=None,
        city="city",
        niche="niche",
        limit=10,
        pack_id="pid-sellable",
        base_dir=tmp_path,
        output_csv=tmp_path / "out.csv",
        output_jsonl=tmp_path / "out.jsonl",
        businesses=businesses,
        status="OK",
        enrichment_tier="basic",
    )

    assert summary["sellable"] is True
    assert summary["quality_gate_failures"] == []

    artifact = json.loads(summary["summary_path"].read_text())
    assert artifact["sellable"] is True
    assert artifact["quality_gate_failures"] == []


def test_generate_pack_sorts_failure_reasons_deterministically(monkeypatch, tmp_path):
    _patch_pipeline(monkeypatch, DummyAnalysis(has_website=False))

    businesses = [_lead(name="Biz", website=None, phone=None, email=None)]

    monkeypatch.setattr(
        "leadgen.generator.check_quality_gates",
        lambda rows, target_count, enriched: (
            False,
            {
                "zeta_failure",
                "alpha_failure",
            },
        ),
    )

    summary = generate_pack(
        query="q",
        country="usa",
        state="fl",
        county=None,
        city="city",
        niche="niche",
        limit=10,
        pack_id="pid-unsellable-order",
        base_dir=tmp_path,
        output_csv=tmp_path / "out.csv",
        output_jsonl=tmp_path / "out.jsonl",
        businesses=businesses,
        status="OK",
        enrichment_tier="basic",
    )

    assert summary["sellable"] is False
    assert summary["quality_gate_failures"] == ["alpha_failure", "zeta_failure"]


def test_generate_pack_forces_unsellable_when_failures_exist_even_if_gate_returns_true(monkeypatch, tmp_path):
    _patch_pipeline(monkeypatch, DummyAnalysis(has_website=True))

    businesses = [_lead(name="Biz", website="https://biz.example.com", phone="(555) 123-4567", email="hi@biz.co")]

    monkeypatch.setattr(
        "leadgen.generator.check_quality_gates",
        lambda rows, target_count, enriched: (True, ["synthetic_gate_failure"]),
    )

    summary = generate_pack(
        query="q",
        country="usa",
        state="fl",
        county=None,
        city="city",
        niche="niche",
        limit=10,
        pack_id="pid-fail-closed",
        base_dir=tmp_path,
        output_csv=tmp_path / "out.csv",
        output_jsonl=tmp_path / "out.jsonl",
        businesses=businesses,
        status="OK",
        enrichment_tier="basic",
    )

    assert summary["sellable"] is False
    assert summary["quality_gate_failures"] == ["synthetic_gate_failure"]

    artifact = json.loads(summary["summary_path"].read_text())
    assert artifact["sellable"] is False
    assert artifact["quality_gate_failures"] == ["synthetic_gate_failure"]


def test_generate_pack_injects_default_reason_if_unsellable_without_failures(monkeypatch, tmp_path):
    _patch_pipeline(monkeypatch, DummyAnalysis(has_website=False))

    businesses = [_lead(name="Biz", website=None, phone=None, email=None)]

    monkeypatch.setattr(
        "leadgen.generator.check_quality_gates",
        lambda rows, target_count, enriched: (False, []),
    )

    summary = generate_pack(
        query="q",
        country="usa",
        state="fl",
        county=None,
        city="city",
        niche="niche",
        limit=10,
        pack_id="pid-unsellable-default-reason",
        base_dir=tmp_path,
        output_csv=tmp_path / "out.csv",
        output_jsonl=tmp_path / "out.jsonl",
        businesses=businesses,
        status="OK",
        enrichment_tier="basic",
    )

    assert summary["sellable"] is False
    assert summary["quality_gate_failures"] == ["quality_gate_failed_without_explicit_reason"]

    artifact = json.loads(summary["summary_path"].read_text())
    assert artifact["quality_gate_failures"] == ["quality_gate_failed_without_explicit_reason"]

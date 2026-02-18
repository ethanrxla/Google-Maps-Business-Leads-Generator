import pytest
from pathlib import Path

import cli
import leadgen.generator as generator
from leadgen.models import Business, WebsiteAnalysis


def _sample_business():
    return Business(
        name="Sample Biz",
        address="123 Main",
        website="https://sample.test",
        place_id="pid-1",
    )


def _sample_analysis():
    return WebsiteAnalysis(
        has_website=True,
        needs_website=False,
        needs_redesign=False,
        needs_chatbot=True,
        needs_ai_integration=True,
        raw_data={},
    )


def _analysis_with_no_needs():
    return WebsiteAnalysis(
        has_website=True,
        needs_website=False,
        needs_redesign=False,
        needs_chatbot=False,
        needs_ai_integration=False,
        raw_data={},
    )


def test_cli_successful_run(monkeypatch):
    called = {}

    def fake_search(query, limit, include_status=False, **kwargs):
        called["search"] = (query, limit, include_status)
        return ([_sample_business()], "OK")

    monkeypatch.setattr(cli, "search_places", fake_search)
    monkeypatch.setattr(generator, "get_details", lambda b: b)
    monkeypatch.setattr(generator, "fetch_html", lambda url: "<html>ok</html>")
    monkeypatch.setattr(generator, "extract_emails", lambda html: [])
    monkeypatch.setattr(generator, "apply_email_patterns", lambda b: None)
    monkeypatch.setattr(generator, "analyze_html", lambda html: _sample_analysis())

    def fake_export_csv(results, output):
        called["export"] = (results, output)

    def fake_export_jsonl(results, output):
        called["export_jsonl"] = (results, output)

    monkeypatch.setattr(generator, "export_csv", fake_export_csv)
    monkeypatch.setattr(generator, "export_jsonl", fake_export_jsonl)

    code = cli.run_cli(["--query", "pizza", "--limit", "5", "--output", "custom.csv"])

    assert code == 0
    assert called["search"] == ("pizza", 5, True)
    results, output_path = called["export"]
    assert output_path == "custom.csv"
    assert len(results) == 1
    assert results[0].business.name == "Sample Biz"
    assert "export_jsonl" not in called


def test_cli_no_leads_prints_message(monkeypatch, capsys):
    def fake_search(query, limit, include_status=False, **kwargs):
        return ([], "ZERO_RESULTS")

    def fake_export(*args, **kwargs):
        raise AssertionError("export_csv should not be called when no leads")

    monkeypatch.setattr(cli, "search_places", fake_search)
    monkeypatch.setattr(generator, "export_csv", fake_export)

    code = cli.run_cli(["-q", "nowhere"])

    assert code == 0
    captured = capsys.readouterr()
    assert "No leads found for query 'nowhere'." in captured.out


def test_cli_missing_required_query_exits():
    with pytest.raises(SystemExit):
        cli.run_cli([])


def test_cli_warns_on_api_error(monkeypatch, caplog):
    caplog.set_level("WARNING")

    def fake_search(query, limit, include_status=False, **kwargs):
        return ([], "OVER_QUERY_LIMIT")

    def fake_export_jsonl(*args, **kwargs):
        raise AssertionError("export_jsonl should not be called on error status")

    monkeypatch.setattr(cli, "search_places", fake_search)
    monkeypatch.setattr(generator, "export_jsonl", fake_export_jsonl)

    code = cli.run_cli(["-q", "limited"])

    assert code == 0
    assert any("OVER_QUERY_LIMIT" in msg for msg in caplog.messages)


def test_cli_exports_website_and_phone(monkeypatch, tmp_path):
    output_file = tmp_path / "leads.csv"

    biz = Business(
        name="Biz",
        address="Addr",
        website=None,
        phone=None,
        place_id="pid",
    )

    def fake_search(query, limit, include_status=False, **kwargs):
        return ([biz], "OK")

    def fake_get_details(business, **kwargs):
        business.website = "https://biz.test"
        business.phone = "555-9999"
        return business

    def fake_fetch_html(url):
        return "<html></html>"

    def fake_extract_emails(html):
        return []

    def fake_analyze(html):
        return _analysis_with_no_needs()

    monkeypatch.setattr(cli, "search_places", fake_search)
    monkeypatch.setattr(generator, "get_details", fake_get_details)
    monkeypatch.setattr(generator, "fetch_html", fake_fetch_html)
    monkeypatch.setattr(generator, "extract_emails", fake_extract_emails)
    monkeypatch.setattr(generator, "analyze_html", fake_analyze)

    code = cli.run_cli(["--query", "q", "--limit", "1", "--output", str(output_file)])

    assert code == 0
    assert output_file.exists()

    import csv

    with output_file.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    assert len(rows) == 1
    row = rows[0]
    assert row["website"] == "https://biz.test"
    assert row["phone"] == "555-9999"


def test_cli_pack_paths_used_when_no_output(monkeypatch, tmp_path):
    called = {}

    def fake_search(query, limit, include_status=False, **kwargs):
        biz = Business(name="Biz", address="Addr", website="https://site", phone="111", place_id="pid")
        return ([biz], "OK")

    def fake_get_details(business, **kwargs):
        return business

    def fake_fetch_html(url):
        return "<html></html>"

    def fake_extract_emails(html):
        return []

    def fake_analyze(html):
        return _analysis_with_no_needs()

    def fake_export_csv(results, output):
        called["csv_output"] = output

    def fake_export_jsonl(results, output):
        called["jsonl_output"] = output

    def fake_build_pack_paths(base_dir, country, state, county, city, niche, default_basename):
        return (
            tmp_path / "packs" / "csv" / f"{default_basename}.csv",
            tmp_path / "packs" / "jsonl" / f"{default_basename}.jsonl",
        )

    monkeypatch.setattr(cli, "search_places", fake_search)
    monkeypatch.setattr(generator, "get_details", fake_get_details)
    monkeypatch.setattr(generator, "fetch_html", fake_fetch_html)
    monkeypatch.setattr(generator, "extract_emails", fake_extract_emails)
    monkeypatch.setattr(generator, "analyze_html", fake_analyze)
    monkeypatch.setattr(generator, "export_csv", fake_export_csv)
    monkeypatch.setattr(generator, "export_jsonl", fake_export_jsonl)
    monkeypatch.setattr(cli, "build_pack_paths", fake_build_pack_paths)

    code = cli.run_cli(
        [
            "--query",
            "restaurants in Boca Raton, FL",
            "--country",
            "usa",
            "--state",
            "florida",
            "--city",
            "boca raton",
            "--niche",
            "restaurants",
        ]
    )

    assert code == 0
    assert "csv_output" in called
    assert "jsonl_output" in called
    assert called["csv_output"].endswith(".csv")
    assert called["jsonl_output"].endswith(".jsonl")
    assert (tmp_path / "packs" / "csv").exists()
    assert (tmp_path / "packs" / "jsonl").exists()


def test_cli_explicit_output_overrides_pack_paths(monkeypatch, tmp_path):
    called = {}
    explicit_csv = tmp_path / "explicit.csv"

    def fake_search(query, limit, include_status=False, **kwargs):
        biz = Business(name="Biz", address="Addr", website="https://site", phone="111", place_id="pid")
        return ([biz], "OK")

    def fake_get_details(business, **kwargs):
        return business

    def fake_fetch_html(url):
        return "<html></html>"

    def fake_extract_emails(html):
        return []

    def fake_analyze(html):
        return _analysis_with_no_needs()

    def fake_export_csv(results, output):
        called["csv_output"] = output

    def fake_export_jsonl(results, output):
        called["jsonl_output"] = output

    def fake_build_pack_paths(*args, **kwargs):
        raise AssertionError("build_pack_paths should not be called when output provided")

    monkeypatch.setattr(cli, "search_places", fake_search)
    monkeypatch.setattr(generator, "get_details", fake_get_details)
    monkeypatch.setattr(generator, "fetch_html", fake_fetch_html)
    monkeypatch.setattr(generator, "extract_emails", fake_extract_emails)
    monkeypatch.setattr(generator, "analyze_html", fake_analyze)
    monkeypatch.setattr(generator, "export_csv", fake_export_csv)
    monkeypatch.setattr(generator, "export_jsonl", fake_export_jsonl)
    monkeypatch.setattr(cli, "build_pack_paths", fake_build_pack_paths)

    code = cli.run_cli(
        [
            "--query",
            "restaurants in Boca Raton, FL",
            "--output",
            str(explicit_csv),
            "--country",
            "usa",
            "--state",
            "florida",
            "--city",
            "boca raton",
            "--niche",
            "restaurants",
        ]
    )

    assert code == 0
    assert called["csv_output"] == str(explicit_csv)
    assert "jsonl_output" not in called

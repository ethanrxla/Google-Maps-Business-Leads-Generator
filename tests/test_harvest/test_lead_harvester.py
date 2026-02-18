from core.lead_harvester import LeadHarvester


def test_lead_harvester_search_returns_leads(harvest_config):
    harvester = LeadHarvester(config=harvest_config)
    results = harvester.search(query="tech companies", limit=5)

    assert isinstance(results, list)
    assert len(results) <= 5
    for lead in results:
        assert isinstance(lead, dict)
        assert "company_name" in lead
        assert "domain" in lead


def test_lead_harvester_respects_limit(harvest_config):
    harvester = LeadHarvester(config=harvest_config)
    results = harvester.search(query="software", limit=2)
    assert len(results) == 2


def test_lead_harvester_handles_empty_sources(harvest_config, monkeypatch):
    harvester = LeadHarvester(config=harvest_config)
    monkeypatch.setattr(harvester, "_mock_source_results", lambda q, limit: [])
    results = harvester.search(query="nonexistent", limit=3)
    assert results == []

from core.data_enricher import DataEnricher


def test_data_enricher_enrich_basic(harvest_config, mock_integrations):
    enricher = DataEnricher(config=harvest_config)
    lead = {"company_name": "Example Corp", "domain": "example.com"}
    enriched = enricher.enrich(lead)
    assert enriched["company_name"] == "Example Corp"
    assert enriched["domain"] == "example.com"
    assert "emails" in enriched

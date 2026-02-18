from core.contact_analyzer import ContactAnalyzer


def test_contact_analyzer_exists():
    analyzer = ContactAnalyzer()
    contacts = [{"email": "a@example.com"}]
    analyzed = analyzer.analyze(contacts)
    assert isinstance(analyzed, list)
    assert analyzed[0]["email"] == "a@example.com"

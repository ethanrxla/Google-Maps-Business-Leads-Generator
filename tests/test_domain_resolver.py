"""Tests for pipeline/domain_resolver.py -- canonical domain resolution."""

import pytest

from pipeline.domain_resolver import (
    DomainResolution,
    REASON_EMPTY_INPUT,
    REASON_NO_DOMAIN_PARSED,
    REASON_IP_ADDRESS,
    REASON_LOCAL_DOMAIN,
    REASON_INVALID_TLD,
    resolve_domain,
)


class TestResolveDomain:
    """Core resolution logic."""

    def test_standard_url(self):
        r = resolve_domain("https://www.dentistmiami.com/contact")
        assert r.resolved_domain == "dentistmiami.com"
        assert r.resolved_url_ok is True
        assert r.resolver_method == "urlparse"
        assert "www_stripped" in r.resolver_notes
        assert r.unresolved_reason is None

    def test_no_scheme(self):
        r = resolve_domain("example.com")
        assert r.resolved_domain == "example.com"
        assert r.resolver_method == "urlparse_heuristic"
        assert "scheme_inferred" in r.resolver_notes

    def test_http_url(self):
        r = resolve_domain("http://mysite.org")
        assert r.resolved_domain == "mysite.org"
        assert r.resolver_method == "urlparse"

    def test_with_port(self):
        r = resolve_domain("https://mysite.com:8080/page")
        assert r.resolved_domain == "mysite.com"

    def test_subdomain_preserved(self):
        r = resolve_domain("https://shop.mybiz.com")
        assert r.resolved_domain == "shop.mybiz.com"

    def test_www_stripped(self):
        r = resolve_domain("https://www.mybiz.com")
        assert r.resolved_domain == "mybiz.com"

    def test_trailing_slash(self):
        r = resolve_domain("https://mybiz.com/")
        assert r.resolved_domain == "mybiz.com"

    def test_query_params_stripped(self):
        r = resolve_domain("https://mybiz.com/page?utm_source=google")
        assert r.resolved_domain == "mybiz.com"

    def test_case_normalized(self):
        r = resolve_domain("https://WWW.MyBiz.COM")
        assert r.resolved_domain == "mybiz.com"


class TestUnresolvedReasons:
    """Each unresolved reason has a deterministic taxonomy string."""

    def test_empty_string(self):
        r = resolve_domain("")
        assert r.resolved_domain is None
        assert r.resolved_url_ok is False
        assert r.unresolved_reason == REASON_EMPTY_INPUT

    def test_none(self):
        r = resolve_domain(None)
        assert r.unresolved_reason == REASON_EMPTY_INPUT

    def test_whitespace_only(self):
        r = resolve_domain("   ")
        assert r.unresolved_reason == REASON_EMPTY_INPUT

    def test_ip_address(self):
        r = resolve_domain("http://192.168.1.1/admin")
        assert r.resolved_domain == "192.168.1.1"
        assert r.unresolved_reason == REASON_IP_ADDRESS

    def test_localhost(self):
        r = resolve_domain("http://localhost:3000")
        assert r.unresolved_reason == REASON_LOCAL_DOMAIN

    def test_local_domain(self):
        r = resolve_domain("http://myapp.local")
        assert r.unresolved_reason == REASON_LOCAL_DOMAIN

    def test_invalid_tld(self):
        r = resolve_domain("http://mysite.x")
        assert r.unresolved_reason == REASON_INVALID_TLD


class TestToDict:
    """Serialization for provenance tracking."""

    def test_success_to_dict(self):
        r = resolve_domain("https://test.com")
        d = r.to_dict()
        assert d["resolved_domain"] == "test.com"
        assert d["resolved_url_ok"] is True
        assert d["resolver_method"] == "urlparse"
        assert d["unresolved_reason"] is None
        assert "input_url" in d

    def test_failure_to_dict(self):
        r = resolve_domain("")
        d = r.to_dict()
        assert d["resolved_domain"] is None
        assert d["resolved_url_ok"] is False
        assert d["unresolved_reason"] == "empty_input"


class TestEdgeCases:
    """Real-world URLs from the existing dataset."""

    def test_google_maps_utm(self):
        url = "https://www.relaxandsmile.com/?utm_source=GMB&utm_medium=organic"
        r = resolve_domain(url)
        assert r.resolved_domain == "relaxandsmile.com"

    def test_wix_site(self):
        r = resolve_domain("https://www.whitesmilesofboca.com/")
        assert r.resolved_domain == "whitesmilesofboca.com"

    def test_bare_domain_no_tld(self):
        r = resolve_domain("notadomain")
        assert r.unresolved_reason == REASON_INVALID_TLD

    def test_co_uk_tld(self):
        r = resolve_domain("https://mysite.co.uk")
        assert r.resolved_domain == "mysite.co.uk"
        assert r.resolved_url_ok is True

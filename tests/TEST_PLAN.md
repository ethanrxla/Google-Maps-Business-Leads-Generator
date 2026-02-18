
```markdown
# Test Plan and Behavior Checklist

This document outlines the testable behaviors and edge cases for the lead generation project, derived from the diagnostic report.

## `leadgen/models.py`

- [ ] `Business` dataclass correctly initializes with valid data.
- [ ] `Business` dataclasses raises a `TypeError` if required fields like `name` are missing.
- [ ] `WebsiteAnalysis` dataclass correctly sets default `False` values.
- [ ] `LeadResult` correctly combines `Business` and `WebsiteAnalysis` instances.

## `leadgen/places.py`

- [ ] `search_places()` successfully returns a list of `Business` objects for a valid query.
- [ ] `search_places()` handles API responses with a non-"OK" status (e.g., `OVER_QUERY_LIMIT`, `REQUEST_DENIED`, `ZERO_RESULTS`) gracefully, returning an empty list or raising a specific error.
- [ ] `search_places()` handles network errors (e.g., connection timeout) without crashing.
- [ ] `search_places()` handles malformed JSON responses from the API.
- [ ] `search_places()` respects the `limit` parameter.
- [ ] `get_details()` successfully populates the `website` and `address` fields for a `Business` object.
- [ ] `get_details()` handles API errors gracefully if the place ID is invalid or the API call fails.
- [ ] `get_details()` handles cases where a place has no website or formatted address in the API response.
- [ ] Handles Google Places results that are missing optional fields (e.g., `website`, `formatted_address`) without crashing.
- [ ] Handles Google Places results that are missing a required field like `name`.

## `leadgen/website_fetch.py`

- [ ] `fetch_html()` returns HTML content for a valid, accessible URL.
- [ ] `fetch_html()` returns `None` for a URL that returns a non-200 status code (e.g., 404, 500).
- [ ] `fetch_html()` returns `None` when a request times out.
- [ ] `fetch_html()` returns `None` for invalid URL formats (e.g., "not-a-url", "", `None`).
- [ ] `fetch_html()` handles `requests.RequestException` and other connection errors.
- [ ] `fetch_html()` correctly uses the custom User-Agent header.

## `leadgen/analysis.py`

- [ ] `analyze_html()` returns `needs_website=True` when the input HTML is `None` or empty.
- [ ] `analyze_html()` correctly identifies a responsive site (has `<meta name="viewport">`).
- [ ] `analyze_html()` correctly flags a site as needing redesign (no viewport tag).
- [ ] `analyze_html()` detects the presence of modern frameworks (Bootstrap, Tailwind).
- [ ] `analyze_html()` detects the absence of modern frameworks.
- [ ] `analyze_html()` detects the presence of a chat widget (Tawk.to, Intercom, etc.).
- [ ] `analyze_html()` detects the absence of a chat widget.
- [ ] `analyze_html()` detects the presence of recent dates (2022-2026).
- [ ] `analyze_html()` detects the presence of AI-related keywords.

## `leadgen/export.py`

- [ ] `export_csv()` creates a CSV file with the correct headers and data for a list of `LeadResult` objects.
- [ ] `export_csv()` handles an empty list of results gracefully (creates an empty file or a file with only headers).
- [ ] `export_csv()` correctly handles data with special characters (e.g., commas, quotes) in fields.
- [ ] `export_csv()` raises an error or handles cases where the output path is not writable.

## `cli.py`

- [ ] The script runs successfully with a `--query` argument.
- [ ] The script exits with an error if the `--query` argument is missing.
- [ ] The script uses the default output path (`data/outputs/leads.csv`) when `--output` is not provided.
- [ ] The script uses the custom output path provided via the `--output` argument.
- [ ] The script respects the `--limit` argument to limit the number of results processed.
- [ ] The main loop completes without error when `search_places` returns an empty list.
- [ ] The script provides clear feedback to the user when no leads are found.
- [ ] The end-to-end flow (search -> details -> fetch -> analyze -> export) works correctly.
```

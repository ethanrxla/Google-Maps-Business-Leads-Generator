
# API Reference: Hunter.io, Apollo.io, BuiltWith, Firecrawl & ScrapingBee

This document provides a comprehensive reference for integrating Hunter.io, Apollo.io, BuiltWith, Firecrawl, and ScrapingBee APIs into your application.

---

## Table of Contents

1. [Hunter.io API](#hunterio-api)

   - [Authentication](#hunter-authentication)
   - [Base URL](#hunter-base-url)
   - [Endpoints](#hunter-endpoints)
   - [Resources](#hunter-resources)
   - [Error Handling](#hunter-error-handling)
   - [Rate Limits](#hunter-rate-limits)
2. [Apollo.io API](#apolloio-api)

   - [Authentication](#apollo-authentication)
   - [Base URL](#apollo-base-url)
   - [Endpoints](#apollo-endpoints)
   - [Error Handling](#apollo-error-handling)
   - [Rate Limits](#apollo-rate-limits)
3. [BuiltWith API](#builtwith-api)

   - [Authentication](#builtwith-authentication)
   - [Base URL](#builtwith-base-url)
   - [Endpoints](#builtwith-endpoints)
   - [Datasets](#builtwith-datasets)
   - [Error Handling](#builtwith-error-handling)
   - [Rate Limits](#builtwith-rate-limits)
4. [Firecrawl API](#firecrawl-api)

   - [Authentication](#firecrawl-authentication)
   - [Base URL](#firecrawl-base-url)
   - [Endpoints](#firecrawl-endpoints)
   - [Error Handling](#firecrawl-error-handling)
   - [Rate Limits](#firecrawl-rate-limits)
5. [ScrapingBee API](#scrapingbee-api)

   - [Authentication](#scrapingbee-authentication)
   - [Base URL](#scrapingbee-base-url)
   - [Endpoints](#scrapingbee-endpoints)
   - [Parameters](#scrapingbee-parameters)
   - [Error Handling](#scrapingbee-error-handling)
   - [Rate Limits](#scrapingbee-rate-limits)

---

## Hunter.io API

### Hunter Authentication

Hunter.io requires an API key for authentication. You can provide it in three ways:

1. **Query Parameter**: `?api_key=YOUR_API_KEY`
2. **Header**: `X-API-KEY: YOUR_API_KEY`
3. **Authorization Header**: `Authorization: Bearer YOUR_API_KEY`

**Test API Key**: Use `test-api-key` for testing (returns dummy responses)

**Get API Key**: Sign up at [Hunter.io](https://hunter.io) and retrieve your key from the dashboard.

### Hunter Base URL

```
https://api.hunter.io/v2/
```

### Hunter Response Structure

All successful responses follow this structure:

```json
{
  "data": {
    // Requested data
  },
  "meta": {
    // Metadata about the request
  }
}
```

Error responses:

```json
{
  "errors": [
    {
      "id": "error_id",
      "code": 400,
      "details": "Error description"
    }
  ]
}
```

### Hunter Endpoints

#### 1. Discover

**Purpose**: Returns companies matching a set of criteria (free endpoint)

**Endpoint**: `GET /discover`

**Parameters**:

- `query` (string, optional): Natural language search query (e.g., "Companies in Europe in the Tech Industry")
- `organization` (object, optional): Filter by domains and/or company names
- `similar_to` (string, optional): Find similar companies (Premium only)
- `headquarters_location` (object, optional): Filter by location (continent, business_region, country, state, city)
- `industry` (array, optional): Filter by industries
- `company_size` (object, optional): Filter by employee count
- `limit` (integer, optional): Results per page (1-100, default: 10)
- `offset` (integer, optional): Pagination offset (Premium only)

**Example Request**:

```
GET https://api.hunter.io/v2/discover?query=Tech companies in San Francisco&limit=20&api_key=YOUR_API_KEY
```

#### 2. Domain Search

**Purpose**: Returns all email addresses found for a given domain

**Endpoint**: `GET /domain-search`

**Parameters**:

- `domain` (string, required): Domain name to search
- `company` (string, optional): Company name
- `limit` (integer, optional): Results per page (1-100, default: 10)
- `offset` (integer, optional): Pagination offset
- `seniority` (array, optional): Filter by seniority level
- `department` (array, optional): Filter by department

**Example Request**:

```
GET https://api.hunter.io/v2/domain-search?domain=stripe.com&api_key=YOUR_API_KEY
```

#### 3. Email Finder

**Purpose**: Finds the most likely email address from a domain, first name, and last name

**Endpoint**: `GET /email-finder`

**Parameters**:

- `domain` (string, required): Domain name
- `first_name` (string, required): First name
- `last_name` (string, required): Last name

**Example Request**:

```
GET https://api.hunter.io/v2/email-finder?domain=stripe.com&first_name=Patrick&last_name=Collison&api_key=YOUR_API_KEY
```

#### 4. Email Verifier

**Purpose**: Checks deliverability and validity of an email address

**Endpoint**: `GET /email-verifier`

**Parameters**:

- `email` (string, required): Email address to verify

**Example Request**:

```
GET https://api.hunter.io/v2/email-verifier?email=patrick@stripe.com&api_key=YOUR_API_KEY
```

**Response Fields**:

- `result`: "deliverable", "undeliverable", "risky", "unknown"
- `score`: Confidence score (0-100)
- `sources`: Array of sources where email was found

#### 5. Enrichment

**Purpose**: Returns all information about a person or company

**Endpoint**: `GET /enrichment`

**Parameters**:

- `email` (string, optional): Email address
- `domain` (string, optional): Domain name
- `company` (string, optional): Company name
- `first_name` (string, optional): First name
- `last_name` (string, optional): Last name

**Example Request**:

```
GET https://api.hunter.io/v2/enrichment?email=patrick@stripe.com&api_key=YOUR_API_KEY
```

#### 6. Email Count

**Purpose**: Returns the number of email addresses found for a domain

**Endpoint**: `GET /email-count`

**Parameters**:

- `domain` (string, required): Domain name

**Example Request**:

```
GET https://api.hunter.io/v2/email-count?domain=stripe.com&api_key=YOUR_API_KEY
```

#### 7. Account Information

**Purpose**: Returns information about your Hunter account

**Endpoint**: `GET /account`

**Example Request**:

```
GET https://api.hunter.io/v2/account?api_key=YOUR_API_KEY
```

### Hunter Resources

#### Leads

**List Leads**: `GET /leads`

- Parameters: `limit`, `offset`, `list_id`, `archived`

**Get Lead**: `GET /leads/{id}`

**Create Lead**: `POST /leads`

- Body: `email`, `first_name`, `last_name`, `company`, `position`, `website`, `list_id`, `custom_attributes`

**Update Lead**: `PATCH /leads/{id}`

- Body: Same as create (all fields optional)

**Delete Lead**: `DELETE /leads/{id}`

#### Custom Attributes

**List Attributes**: `GET /custom_attributes`

**Create Attribute**: `POST /custom_attributes`

- Body: `name`, `type` (text, number, date, boolean, url, email)

**Update Attribute**: `PATCH /custom_attributes/{id}`

- Body: `name`, `type`

**Delete Attribute**: `DELETE /custom_attributes/{id}`

#### Leads Lists

**List Lists**: `GET /leads_lists`

**Get List**: `GET /leads_lists/{id}`

**Create List**: `POST /leads_lists`

- Body: `name`

**Update List**: `PATCH /leads_lists/{id}`

- Body: `name`

**Delete List**: `DELETE /leads_lists/{id}`

#### Campaigns

**List Campaigns**: `GET /campaigns`

- Parameters: `limit`, `offset`

**Get Campaign**: `GET /campaigns/{id}`

**Create Campaign**: `POST /campaigns`

- Body: `name`, `subject`, `content`, `sender_email`, `sender_name`, `reply_to`

**Update Campaign**: `PATCH /campaigns/{id}`

- Body: Same as create (all fields optional)

**Delete Campaign**: `DELETE /campaigns/{id}`

**List Recipients**: `GET /campaigns/{id}/recipients`

- Parameters: `limit`, `offset`

**Add Recipients**: `POST /campaigns/{id}/recipients`

- Body: `emails` (array or string), `lead_ids` (array)

**Cancel Scheduled Emails**: `DELETE /campaigns/{id}/recipients`

- Body: `emails` (array or string)

**Start Campaign**: `POST /campaigns/{id}/start`

### Hunter Error Handling

| Status Code | Meaning                                                            |
| ----------- | ------------------------------------------------------------------ |
| 200         | OK - Request successful                                            |
| 201         | Created - Resource created successfully                            |
| 204         | No Content - Request successful, no content returned               |
| 400         | Bad Request - Missing or invalid parameter                         |
| 401         | Unauthorized - No valid API key provided                           |
| 403         | Forbidden - Rate limit reached                                     |
| 404         | Not Found - Resource does not exist                                |
| 422         | Unprocessable Entity - Valid request but creation failed           |
| 429         | Too Many Requests - Usage limit reached                            |
| 451         | Unavailable for Legal Reasons - Data processing stopped by request |
| 5XX         | Server Error - Error on Hunter's end                               |

### Hunter Rate Limits

Rate limits vary by plan. Check your account dashboard for specific limits. Free tier has limited requests per month.

---

## Apollo.io API

### Apollo Authentication

Apollo.io supports two authentication methods:

1. **API Key Authentication**:

   - Generate API key from Apollo account settings
   - Include in request headers: `X-Api-Key: YOUR_API_KEY`
   - Or use: `Authorization: Bearer YOUR_API_KEY`
2. **OAuth 2.0**:

   - For integrations acting on behalf of Apollo users
   - Follow OAuth 2.0 authorization flow
   - See [Apollo OAuth Documentation](https://docs.apollo.io/reference/authentication)

**Get API Key**: Generate from your Apollo account settings.

### Apollo Base URL

```
https://api.apollo.io/v1/
```

### Apollo Endpoints

#### 1. People Enrichment

**Purpose**: Enhance person records with additional data

**Endpoint**: `POST /mixed_people/match`

**Parameters** (JSON body):

- `email` (string, optional): Email address
- `first_name` (string, optional): First name
- `last_name` (string, optional): Last name
- `organization_name` (string, optional): Organization name
- `domain` (string, optional): Domain name

**Example Request**:

```json
POST https://api.apollo.io/v1/mixed_people/match
Headers: {
  "X-Api-Key": "YOUR_API_KEY",
  "Content-Type": "application/json"
}
Body: {
  "email": "patrick@stripe.com",
  "first_name": "Patrick",
  "last_name": "Collison"
}
```

#### 2. Bulk People Enrichment

**Purpose**: Enrich multiple people records at once

**Endpoint**: `POST /mixed_people/bulk_match`

**Parameters** (JSON body):

- `people` (array, required): Array of person objects with same fields as single enrichment

**Example Request**:

```json
POST https://api.apollo.io/v1/mixed_people/bulk_match
Body: {
  "people": [
    {
      "email": "person1@example.com",
      "first_name": "John",
      "last_name": "Doe"
    },
    {
      "email": "person2@example.com",
      "first_name": "Jane",
      "last_name": "Smith"
    }
  ]
}
```

#### 3. Organization Enrichment

**Purpose**: Retrieve detailed information about organizations

**Endpoint**: `POST /mixed_people/match_organization`

**Parameters** (JSON body):

- `domain` (string, optional): Domain name
- `organization_name` (string, optional): Organization name
- `organization_id` (string, optional): Apollo organization ID

**Example Request**:

```json
POST https://api.apollo.io/v1/mixed_people/match_organization
Body: {
  "domain": "stripe.com",
  "organization_name": "Stripe"
}
```

#### 4. Bulk Organization Enrichment

**Purpose**: Enrich multiple organizations at once

**Endpoint**: `POST /mixed_people/bulk_match_organization`

**Parameters** (JSON body):

- `organizations` (array, required): Array of organization objects

#### 5. People API Search

**Purpose**: Search for individuals based on various filters

**Endpoint**: `POST /mixed_people/search`

**Parameters** (JSON body):

- `q_keywords` (string, optional): Keywords search
- `person_titles` (array, optional): Job titles
- `person_locations` (array, optional): Locations
- `organization_domains` (array, optional): Organization domains
- `organization_names` (array, optional): Organization names
- `page` (integer, optional): Page number (default: 1)
- `per_page` (integer, optional): Results per page (default: 25, max: 100)

**Example Request**:

```json
POST https://api.apollo.io/v1/mixed_people/search
Body: {
  "person_titles": ["CEO", "CTO"],
  "organization_domains": ["stripe.com"],
  "page": 1,
  "per_page": 50
}
```

#### 6. Organization Search

**Purpose**: Find organizations matching specific criteria

**Endpoint**: `POST /organizations/search`

**Parameters** (JSON body):

- `q_keywords` (string, optional): Keywords search
- `organization_locations` (array, optional): Locations
- `organization_num_employees_ranges` (array, optional): Employee count ranges
- `organization_industries` (array, optional): Industries
- `page` (integer, optional): Page number
- `per_page` (integer, optional): Results per page

**Example Request**:

```json
POST https://api.apollo.io/v1/organizations/search
Body: {
  "q_keywords": "fintech",
  "organization_num_employees_ranges": ["51,200"],
  "organization_locations": ["San Francisco, California, United States"]
}
```

#### 7. Organization Jobs Postings

**Purpose**: Get job postings for an organization

**Endpoint**: `GET /organizations/{organization_id}/jobs`

**Parameters**:

- `organization_id` (string, required): Apollo organization ID
- `page` (integer, optional): Page number
- `per_page` (integer, optional): Results per page

**Example Request**:

```
GET https://api.apollo.io/v1/organizations/ORG_ID/jobs?page=1&per_page=25
```

#### 8. Get Complete Organization Info

**Purpose**: Retrieve comprehensive information about an organization

**Endpoint**: `GET /organizations/{organization_id}`

**Parameters**:

- `organization_id` (string, required): Apollo organization ID

**Example Request**:

```
GET https://api.apollo.io/v1/organizations/ORG_ID
```

#### 9. News Articles Search

**Purpose**: Search for news articles related to organizations or people

**Endpoint**: `POST /news_articles/search`

**Parameters** (JSON body):

- `q_keywords` (string, optional): Keywords search
- `organization_ids` (array, optional): Organization IDs
- `person_ids` (array, optional): Person IDs
- `page` (integer, optional): Page number
- `per_page` (integer, optional): Results per page

**Example Request**:

```json
POST https://api.apollo.io/v1/news_articles/search
Body: {
  "organization_ids": ["ORG_ID_1", "ORG_ID_2"],
  "page": 1,
  "per_page": 20
}
```

### Apollo Error Handling

Apollo.io uses standard HTTP status codes:

| Status Code | Meaning                                               |
| ----------- | ----------------------------------------------------- |
| 200         | OK - Request successful                               |
| 201         | Created - Resource created successfully               |
| 400         | Bad Request - Invalid request parameters              |
| 401         | Unauthorized - Invalid or missing API key             |
| 403         | Forbidden - Insufficient permissions                  |
| 404         | Not Found - Resource does not exist                   |
| 429         | Too Many Requests - Rate limit exceeded               |
| 500         | Internal Server Error - Error on Apollo's end         |
| 503         | Service Unavailable - Service temporarily unavailable |

**Error Response Format**:

```json
{
  "error": {
    "message": "Error description",
    "code": "ERROR_CODE"
  }
}
```

### Apollo Rate Limits

Rate limits vary by plan tier. Check your Apollo account for specific limits. Common limits:

- **Free Tier**: Limited requests per month
- **Paid Tiers**: Higher limits based on subscription

**Rate Limit Headers**:

- `X-RateLimit-Limit`: Total requests allowed
- `X-RateLimit-Remaining`: Remaining requests
- `X-RateLimit-Reset`: Time when limit resets

---

## BuiltWith API

### BuiltWith Authentication

BuiltWith requires an API key for authentication. Include it as a query parameter:

- **Query Parameter**: `KEY=YOUR_API_KEY`

**Get API Key**: Sign up at [BuiltWith](https://builtwith.com) and retrieve your key from your account dashboard.

### BuiltWith Base URL

```
https://api.builtwith.com/v14/
```

### BuiltWith Endpoints

#### 1. Technology Lookup

**Purpose**: Retrieve technologies used by a specific domain

**Endpoint**: `GET /api.json`

**Parameters**:

- `KEY` (string, required): Your API key
- `LOOKUP` (string, required): Domain name to analyze (e.g., "example.com")
- `HIDETEXT` (string, optional): Hide text descriptions ("yes" or "no")
- `HIDEDL` (string, optional): Hide download links ("yes" or "no")

**Example Request**:

```
GET https://api.builtwith.com/v14/api.json?KEY=YOUR_API_KEY&LOOKUP=stripe.com
```

**Response**: Returns JSON object with technology data including:

- Technologies detected
- Categories (e.g., Analytics, CMS, Frameworks)
- First and last detected dates
- Technology paths

#### 2. Domain API

**Purpose**: Retrieve a list of domains using a specific technology

**Endpoint**: `GET /api.json`

**Parameters**:

- `KEY` (string, required): Your API key
- `TECH` (string, required): Technology name to search for (e.g., "WordPress", "React")
- `META` (string, optional): Include metadata ("yes" or "no")
- `START` (integer, optional): Starting record for pagination
- `LIMIT` (integer, optional): Number of results (max 1000)

**Example Request**:

```
GET https://api.builtwith.com/v14/api.json?KEY=YOUR_API_KEY&TECH=WordPress&LIMIT=100
```

#### 3. Relationships

**Purpose**: Get related domains based on shared technologies

**Endpoint**: `GET /relationships.json`

**Parameters**:

- `KEY` (string, required): Your API key
- `LOOKUP` (string, required): Domain name to analyze

**Example Request**:

```
GET https://api.builtwith.com/v14/relationships.json?KEY=YOUR_API_KEY&LOOKUP=stripe.com
```

### BuiltWith Datasets

BuiltWith provides bulk datasets in two formats:

1. **Apache Parquet**: Columnar storage format for analytics

   - Efficient compression (75-90% reduction)
   - Fast queries and filtering
   - Best for: Data warehouses, Spark, BI tools
2. **Tab-Separated Values (TSV)**: Flat file format

   - Universal compatibility
   - Human readable
   - Best for: Ad-hoc analysis, ETL scripting

**Popular Datasets**:

- Global Live eCommerce Websites: 1,030,046,014 records
- Global Live Payment Websites: 1,245,475,011 records
- Global Live A/B Testing Websites: 32,226,200 records
- Entire Internet (Live): 14,652,479,091 records

**Data Schema Fields**:

- `Domain`: Website domain
- `Country`: Country code
- `Spend`: Estimated spend
- `Revenue`: Estimated revenue
- `PageRank`, `BwsRank`, `MajesticRank`, `UmbrellaRank`, `TrancoRank`: Ranking metrics
- `Employees`: Number of employees
- `Vertical`: Industry vertical
- `Followers`: Social media followers
- `Sku`: Product SKU count
- `CompanyName`: Company name
- `Telephones`: Array of phone numbers
- `SocialUrls`: Array of social media URLs
- `City`, `State`, `Zip`: Location data
- `FirstIndexed`, `LastIndexed`: Timestamps
- `Techs`: Array of technologies with detection dates

**Dataset Access**: Available through [BuiltWith Datasets](https://builtwith.com/datasets)

### BuiltWith Error Handling

| Status Code | Meaning                                                     |
| ----------- | ----------------------------------------------------------- |
| 200         | OK - Request successful                                     |
| 400         | Bad Request - Invalid parameters                            |
| 401         | Unauthorized - Invalid or missing API key                   |
| 403         | Forbidden - Insufficient permissions or rate limit exceeded |
| 404         | Not Found - Resource does not exist                         |
| 500         | Internal Server Error - Error on BuiltWith's end            |

### BuiltWith Rate Limits

Rate limits vary by plan. Check your BuiltWith account for specific limits. Free tier has limited requests per month.

---

## Firecrawl API

### Firecrawl Authentication

Firecrawl requires an API key for authentication. Include it in the Authorization header:

- **Authorization Header**: `Authorization: Bearer YOUR_API_KEY`

**Get API Key**: Sign up at [Firecrawl](https://firecrawl.dev) and retrieve your key from your account dashboard.

### Firecrawl Base URL

```
https://api.firecrawl.dev
```

### Firecrawl Endpoints

#### 1. Scrape

**Purpose**: Scrape a single URL and extract content

**Endpoint**: `POST /scrape`

**Headers**:

- `Authorization: Bearer YOUR_API_KEY`
- `Content-Type: application/json`

**Parameters** (JSON body):

- `url` (string, required): URL to scrape
- `formats` (array, optional): Output formats - `["markdown", "html", "rawHtml", "screenshot"]`
- `onlyMainContent` (boolean, optional): Extract only main content (default: false)
- `includeTags` (array, optional): HTML tags to include
- `excludeTags` (array, optional): HTML tags to exclude
- `waitFor` (integer, optional): Wait time in milliseconds for page load
- `timeout` (integer, optional): Request timeout in milliseconds

**Example Request**:

```json
POST https://api.firecrawl.dev/scrape
Headers: {
  "Authorization": "Bearer YOUR_API_KEY",
  "Content-Type": "application/json"
}
Body: {
  "url": "https://example.com",
  "formats": ["markdown", "html"],
  "onlyMainContent": true
}
```

**Response**: Returns scraped content in requested formats

#### 2. Batch Scrape

**Purpose**: Scrape multiple URLs in a single request

**Endpoint**: `POST /batch-scrape`

**Parameters** (JSON body):

- `requests` (array, required): Array of scrape request objects (same parameters as single scrape)

**Example Request**:

```json
POST https://api.firecrawl.dev/batch-scrape
Body: {
  "requests": [
    {
      "url": "https://example.com",
      "formats": ["markdown"]
    },
    {
      "url": "https://another.com",
      "formats": ["html"]
    }
  ]
}
```

#### 3. Get Batch Scrape Status

**Purpose**: Check status of a batch scrape job

**Endpoint**: `GET /batch-scrape/{jobId}`

**Parameters**:

- `jobId` (string, required): Batch scrape job ID

**Example Request**:

```
GET https://api.firecrawl.dev/batch-scrape/JOB_ID
```

#### 4. Delete Batch Scrape

**Purpose**: Delete a batch scrape job

**Endpoint**: `DELETE /batch-scrape/{jobId}`

**Parameters**:

- `jobId` (string, required): Batch scrape job ID

#### 5. Get Batch Scrape Errors

**Purpose**: Retrieve errors from a batch scrape job

**Endpoint**: `GET /batch-scrape/{jobId}/errors`

#### 6. Search

**Purpose**: Search for specific content across scraped pages

**Endpoint**: `POST /search`

**Parameters** (JSON body):

- `query` (string, required): Search query
- `urls` (array, optional): URLs to search within
- `limit` (integer, optional): Maximum number of results

**Example Request**:

```json
POST https://api.firecrawl.dev/search
Body: {
  "query": "contact information",
  "urls": ["https://example.com", "https://another.com"]
}
```

#### 7. Map

**Purpose**: Create a sitemap of a website

**Endpoint**: `POST /map`

**Parameters** (JSON body):

- `url` (string, required): Starting URL
- `subdomains` (boolean, optional): Include subdomains (default: false)
- `tld` (boolean, optional): Include different TLDs (default: false)
- `limit` (integer, optional): Maximum pages to map

**Example Request**:

```json
POST https://api.firecrawl.dev/map
Body: {
  "url": "https://example.com",
  "subdomains": false,
  "limit": 100
}
```

#### 8. Crawl (Start)

**Purpose**: Start a crawling job to scrape multiple pages

**Endpoint**: `POST /crawl`

**Parameters** (JSON body):

- `url` (string, required): Starting URL
- `crawlerOptions` (object, optional): Crawling configuration
  - `maxDepth` (integer): Maximum crawl depth
  - `limit` (integer): Maximum pages to crawl
  - `allowBackwardLinks` (boolean): Allow crawling backward links
  - `includeSubdomains` (boolean): Include subdomains
- `scrapeOptions` (object, optional): Scraping configuration (same as scrape endpoint)

**Example Request**:

```json
POST https://api.firecrawl.dev/crawl
Body: {
  "url": "https://example.com",
  "crawlerOptions": {
    "maxDepth": 2,
    "limit": 50
  }
}
```

#### 9. Get Crawl Status

**Purpose**: Check status of a crawl job

**Endpoint**: `GET /crawl/{jobId}`

**Parameters**:

- `jobId` (string, required): Crawl job ID

#### 10. Crawl Params Preview

**Purpose**: Preview crawl parameters before starting a crawl

**Endpoint**: `POST /crawl/params-preview`

**Parameters** (JSON body): Same as crawl endpoint

#### 11. Delete Crawl

**Purpose**: Delete a crawl job

**Endpoint**: `DELETE /crawl/{jobId}`

#### 12. Get Crawl Errors

**Purpose**: Retrieve errors from a crawl job

**Endpoint**: `GET /crawl/{jobId}/errors`

#### 13. Get Active Crawls

**Purpose**: List all active crawl jobs

**Endpoint**: `GET /crawl/active`

#### 14. Extract

**Purpose**: Extract structured data from a URL using AI

**Endpoint**: `POST /extract`

**Parameters** (JSON body):

- `url` (string, required): URL to extract from
- `extractorOptions` (object, required): Extraction configuration
  - `mode` (string): "llm-extract" or "schema"
  - `schema` (object): JSON schema for extraction (if mode is "schema")
  - `prompt` (string): Extraction prompt (if mode is "llm-extract")

**Example Request**:

```json
POST https://api.firecrawl.dev/extract
Body: {
  "url": "https://example.com",
  "extractorOptions": {
    "mode": "llm-extract",
    "prompt": "Extract all product names and prices"
  }
}
```

#### 15. Get Extract Status

**Purpose**: Check status of an extract job

**Endpoint**: `GET /extract/{jobId}`

### Firecrawl Error Handling

| Status Code | Meaning                                          |
| ----------- | ------------------------------------------------ |
| 200         | OK - Request successful                          |
| 201         | Created - Job created successfully               |
| 400         | Bad Request - Invalid parameters                 |
| 401         | Unauthorized - Invalid or missing API key        |
| 403         | Forbidden - Insufficient permissions             |
| 404         | Not Found - Resource does not exist              |
| 429         | Too Many Requests - Rate limit exceeded          |
| 500         | Internal Server Error - Error on Firecrawl's end |

**Error Response Format**:

```json
{
  "error": {
    "message": "Error description",
    "code": "ERROR_CODE"
  }
}
```

### Firecrawl Rate Limits

Rate limits vary by plan. Check your Firecrawl account for specific limits. Free tier has limited requests per month.

---

## ScrapingBee API

### ScrapingBee Authentication

ScrapingBee requires an API key for authentication. Include it as a query parameter:

- **Query Parameter**: `api_key=YOUR_API_KEY`

**Get API Key**: Sign up at [ScrapingBee](https://www.scrapingbee.com) and retrieve your key from your account dashboard.

### ScrapingBee Base URL

```
https://app.scrapingbee.com/api/v1/
```

### ScrapingBee Endpoints

#### 1. Scrape

**Purpose**: Scrape a single URL with various configuration options

**Endpoint**: `GET /`

**Required Parameters**:

- `api_key` (string, required): Your API key
- `url` (string, required): URL to scrape (must be URL encoded)

**Example Request**:

```
GET https://app.scrapingbee.com/api/v1/?api_key=YOUR_API_KEY&url=https%3A%2F%2Fexample.com
```

### ScrapingBee Parameters

All parameters are passed as query parameters in the GET request:

#### JavaScript Rendering

- `render_js` (boolean): Enable JavaScript rendering (`true` or `false`, default: `false`)
- `js_scenario` (string): Custom JavaScript scenario to execute
- `wait` (integer): Wait time in milliseconds before returning content
- `wait_for` (string): CSS selector to wait for before returning content
- `wait_browser` (string): Browser event to wait for: `"load"`, `"domcontentloaded"`, `"networkidle"`

#### Browser Configuration

- `block_ads` (boolean): Block ads (`true` or `false`)
- `block_resources` (string): Comma-separated list of resource types to block: `"image"`, `"stylesheet"`, `"font"`, `"media"`, `"websocket"`, `"other"`
- `window_width` (integer): Browser window width in pixels
- `window_height` (integer): Browser window height in pixels

#### Proxy Configuration

- `premium_proxy` (boolean): Use premium proxy (`true` or `false`)
- `country_code` (string): Two-letter country code for proxy location (e.g., `"US"`, `"GB"`)
- `stealth_proxy` (boolean): Use stealth proxy to avoid detection
- `own_proxy` (string): Use your own proxy server URL

#### Headers

- `forward_headers` (boolean): Forward original request headers
- `forward_headers_pure` (boolean): Forward headers in pure mode

#### Data Extraction

- `extract_rules` (string): JSON-encoded extraction rules

  ```json
  {
    "title": "h1",
    "price": ".price",
    "description": ".description"
  }
  ```
- `ai_extract_rules` (string): AI-powered extraction rules (Beta)
- `ai_query` (string): Natural language query for AI extraction (Beta)
- `ai_selector` (string): CSS selector for AI extraction scope (Beta)

#### Response Formats

- `json_response` (boolean): Return JSON response instead of HTML
- `return_page_source` (boolean): Include page source in response
- `return_page_markdown` (boolean): Return content as Markdown
- `return_page_text` (boolean): Return only text content

#### Screenshots

- `screenshot` (boolean): Take a screenshot (`true` or `false`)
- `screenshot_selector` (string): CSS selector for element screenshot
- `screenshot_full_page` (boolean): Capture full page screenshot

#### PDF Conversion

- `pdf` (boolean): Convert page to PDF (`true` or `false`)

#### Scraping Configuration

- `scraping_config` (string): JSON-encoded scraping configuration object

**Example Request with Multiple Parameters**:

```
GET https://app.scrapingbee.com/api/v1/?api_key=YOUR_API_KEY&url=https%3A%2F%2Fexample.com&render_js=true&wait=3000&block_ads=true&screenshot=true&json_response=true
```

**Response Formats**:

1. **HTML Response** (default): Returns raw HTML content
2. **JSON Response** (`json_response=true`):

```json
{
  "body": "<html>...</html>",
  "status_code": 200,
  "screenshot": "base64_encoded_image"
}
```

3. **Markdown Response** (`return_page_markdown=true`): Returns Markdown formatted content
4. **Text Response** (`return_page_text=true`): Returns plain text content
5. **Screenshot**: Returns image file when `screenshot=true`
6. **PDF**: Returns PDF file when `pdf=true`

### ScrapingBee Error Handling

| Status Code | Meaning                                               |
| ----------- | ----------------------------------------------------- |
| 200         | OK - Request successful                               |
| 400         | Bad Request - Invalid parameters or URL               |
| 401         | Unauthorized - Invalid or missing API key             |
| 402         | Payment Required - Insufficient credits               |
| 403         | Forbidden - Access denied                             |
| 404         | Not Found - URL not found                             |
| 429         | Too Many Requests - Rate limit exceeded               |
| 500         | Internal Server Error - Error on ScrapingBee's end    |
| 503         | Service Unavailable - Service temporarily unavailable |

**Error Response Format**:

```json
{
  "error": "Error message description"
}
```

### ScrapingBee Rate Limits

Rate limits and credits vary by plan:

- **Free Tier**: Limited requests per month
- **Paid Tiers**: Higher limits based on subscription
- Credits are consumed per request (varies by features used)

Check your ScrapingBee account dashboard for current credit balance and limits.

---

## Best Practices

### General

1. **Store API Keys Securely**: Never commit API keys to version control. Use environment variables or secure key management.
2. **Handle Errors Gracefully**: Always implement proper error handling for all API calls.
3. **Respect Rate Limits**: Implement rate limiting and retry logic with exponential backoff.
4. **Cache Responses**: Cache API responses when appropriate to reduce API calls and improve performance.
5. **Use Pagination**: For endpoints that support pagination, implement proper pagination handling.

### Hunter.io Specific

1. **Use Test API Key**: During development, use `test-api-key` to avoid consuming quota.
2. **Batch Operations**: When possible, use bulk endpoints to reduce API calls.
3. **Verify Before Sending**: Use Email Verifier before sending emails to reduce bounce rates.

### Apollo.io Specific

1. **Use Search Filters**: Narrow down searches with specific filters to get better results.
2. **Bulk Operations**: Use bulk enrichment endpoints when processing multiple records.
3. **Test Endpoints**: Use Apollo's interactive testing environment to verify requests before implementation.

### BuiltWith Specific

1. **Cache Technology Lookups**: Technology stacks don't change frequently, so cache results to reduce API calls.
2. **Use Datasets for Bulk Analysis**: For large-scale analysis, consider using BuiltWith datasets instead of individual API calls.
3. **Optimize Domain Searches**: Use specific technology filters when searching for domains to get more relevant results.

### Firecrawl Specific

1. **Use Batch Operations**: When scraping multiple URLs, use batch scrape or crawl endpoints instead of multiple individual requests.
2. **Optimize Formats**: Only request formats you need (markdown, html, etc.) to reduce response size and processing time.
3. **Monitor Job Status**: For long-running jobs, implement polling to check status rather than blocking.
4. **Use Extract for Structured Data**: Use the extract endpoint with AI for structured data extraction instead of manual parsing.

### ScrapingBee Specific

1. **Enable JavaScript Rendering Only When Needed**: JavaScript rendering consumes more credits, so only use it for dynamic content.
2. **Use Screenshots Sparingly**: Screenshots are resource-intensive; use them only when necessary.
3. **Block Unnecessary Resources**: Use `block_resources` to reduce bandwidth and improve speed.
4. **Cache Results**: Cache scraped content when possible since web content doesn't change frequently.
5. **Use Premium Proxies for Difficult Sites**: Some sites require premium proxies to avoid blocking.

---

## Quick Reference

### Hunter.io Common Endpoints

```
GET  /discover              - Find companies
GET  /domain-search         - Get emails for domain
GET  /email-finder          - Find email by name
GET  /email-verifier        - Verify email
GET  /enrichment            - Enrich person/company
GET  /email-count           - Count emails for domain
GET  /account               - Account info
GET  /leads                 - List leads
POST /leads                 - Create lead
GET  /campaigns             - List campaigns
POST /campaigns/{id}/start  - Start campaign
```

### Apollo.io Common Endpoints

```
POST /mixed_people/match              - Enrich person
POST /mixed_people/bulk_match         - Bulk enrich people
POST /mixed_people/match_organization - Enrich organization
POST /mixed_people/search             - Search people
POST /organizations/search            - Search organizations
GET  /organizations/{id}              - Get organization
GET  /organizations/{id}/jobs         - Get jobs
POST /news_articles/search            - Search news
```

### BuiltWith Common Endpoints

```
GET /api.json?LOOKUP=domain          - Technology lookup
GET /api.json?TECH=technology        - Find domains using tech
GET /relationships.json?LOOKUP=domain - Get related domains
```

### Firecrawl Common Endpoints

```
POST /scrape                         - Scrape single URL
POST /batch-scrape                   - Batch scrape URLs
GET  /batch-scrape/{jobId}           - Get batch status
POST /search                         - Search content
POST /map                            - Create sitemap
POST /crawl                          - Start crawl job
GET  /crawl/{jobId}                  - Get crawl status
POST /extract                        - Extract structured data
GET  /extract/{jobId}                - Get extract status
```

### ScrapingBee Common Endpoints

```
GET /?url=URL&api_key=KEY            - Basic scrape
GET /?url=URL&render_js=true        - Scrape with JS
GET /?url=URL&screenshot=true        - Take screenshot
GET /?url=URL&pdf=true               - Convert to PDF
GET /?url=URL&extract_rules=JSON     - Extract data
```

---

## Resources

- **Hunter.io Documentation**: https://hunter.io/api-documentation/v2
- **Apollo.io Documentation**: https://docs.apollo.io/reference
- **BuiltWith API Documentation**: https://api.builtwith.com
- **BuiltWith Datasets**: https://builtwith.com/datasets
- **Firecrawl Documentation**: https://docs.firecrawl.dev/api-reference/introduction
- **ScrapingBee Documentation**: https://www.scrapingbee.com/documentation

**Dashboards**:

- **Hunter.io Dashboard**: https://hunter.io/dashboard
- **Apollo.io Dashboard**: https://app.apollo.io
- **BuiltWith Dashboard**: https://builtwith.com (login required)
- **Firecrawl Dashboard**: https://firecrawl.dev (login required)
- **ScrapingBee Dashboard**: https://www.scrapingbee.com (login required)

---

## Support

For issues or questions:

- **Hunter.io**: Contact through their support channels
- **Apollo.io**: Check documentation or contact support through your account
- **BuiltWith**: Contact support@builtwith.com or through account dashboard
- **Firecrawl**: Check documentation or contact support through your account
- **ScrapingBee**: Check documentation or contact support through your account

---

*Last Updated: Based on API documentation as of 2024*

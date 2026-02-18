# Lead Enrichment Guide: Apollo.io & Hunter.io

This guide explains how batch enrichment works in Apollo.io and Hunter.io, and what additional data you can expect when enriching leads.

---

## Table of Contents

1. [Apollo.io Batch Enrichment](#apolloio-batch-enrichment)
   - [How It Works](#apollo-how-it-works)
   - [Batch Process](#apollo-batch-process)
   - [Response Structure](#apollo-response-structure)
   - [Additional Data Fields](#apollo-additional-data)

2. [Hunter.io Enrichment](#hunterio-enrichment)
   - [How It Works](#hunter-how-it-works)
   - [Enrichment Process](#hunter-enrichment-process)
   - [Response Structure](#hunter-response-structure)
   - [Additional Data Fields](#hunter-additional-data)

3. [Data Comparison](#data-comparison)
4. [Best Practices](#best-practices)

---

## Apollo.io Batch Enrichment

### Apollo: How It Works

Apollo.io's batch enrichment allows you to enrich multiple people or organizations in a single API call. The system matches your input data (email, name, domain, etc.) against Apollo's database of 700+ million contacts and organizations.

#### Batch People Enrichment

**Endpoint**: `POST /mixed_people/bulk_match`

**How It Works**:
1. You send an array of person objects (up to 50 per request)
2. Apollo matches each person against their database
3. Returns enriched profiles with all available data
4. Each person is matched independently - partial matches are still returned

**Request Structure**:
```json
{
  "people": [
    {
      "email": "john@example.com",
      "first_name": "John",
      "last_name": "Doe"
    },
    {
      "email": "jane@company.com",
      "first_name": "Jane",
      "last_name": "Smith",
      "organization_name": "Company Inc"
    }
  ]
}
```

**Response Structure**:
```json
{
  "people": [
    {
      "id": "apollo_person_id_123",
      "first_name": "John",
      "last_name": "Doe",
      "name": "John Doe",
      "title": "Senior Software Engineer",
      "headline": "Full-stack developer with 10+ years experience",
      "email": "john@example.com",
      "emails": [
        {
          "email": "john@example.com",
          "status": "verified"
        }
      ],
      "phone_numbers": [
        {
          "raw_number": "+1-555-123-4567",
          "sanitized_number": "15551234567"
        }
      ],
      "organization": {
        "id": "apollo_org_456",
        "name": "Example Corp",
        "website_url": "https://example.com",
        "industry": "Technology",
        "employee_count": 150,
        "estimated_annual_revenue": 5000000
      },
      "linkedin_url": "https://linkedin.com/in/johndoe",
      "twitter_url": "https://twitter.com/johndoe",
      "github_url": "https://github.com/johndoe",
      "state": "California",
      "city": "San Francisco",
      "country": "United States",
      "postal_code": "94102",
      "timezone": "America/Los_Angeles",
      "experience": [
        {
          "title": "Senior Software Engineer",
          "company": "Example Corp",
          "start_date": "2020-01",
          "end_date": null,
          "description": "Lead development of web applications"
        }
      ],
      "education": [
        {
          "school": "Stanford University",
          "degree": "Bachelor of Science",
          "field_of_study": "Computer Science",
          "start_date": "2010",
          "end_date": "2014"
        }
      ],
      "skills": ["JavaScript", "Python", "React", "Node.js"],
      "languages": ["English", "Spanish"],
      "seniority": "senior",
      "department": "Engineering",
      "functions": ["Engineering", "Product Development"],
      "inferred_salary": {
        "min": 120000,
        "max": 180000
      },
      "inferred_years_experience": 10,
      "profile_picture_url": "https://...",
      "last_updated": "2024-01-15T10:30:00Z"
    }
  ],
  "partial_results": [
    {
      "input": {
        "email": "jane@company.com"
      },
      "match_status": "partial",
      "matched_fields": ["email"],
      "available_data": {
        "name": "Jane Smith",
        "title": "Marketing Director"
      }
    }
  ],
  "not_found": [
    {
      "input": {
        "email": "unknown@example.com"
      },
      "reason": "not_in_database"
    }
  ]
}
```

#### Batch Organization Enrichment

**Endpoint**: `POST /mixed_people/bulk_match_organization`

**How It Works**:
1. Send array of organization identifiers (domain, name, or Apollo ID)
2. Apollo matches and enriches each organization
3. Returns comprehensive company profiles

**Request Structure**:
```json
{
  "organizations": [
    {
      "domain": "stripe.com"
    },
    {
      "organization_name": "Shopify"
    },
    {
      "organization_id": "apollo_org_789"
    }
  ]
}
```

**Response Structure**:
```json
{
  "organizations": [
    {
      "id": "apollo_org_456",
      "name": "Stripe",
      "website_url": "https://stripe.com",
      "domain": "stripe.com",
      "domains": ["stripe.com", "stripe.io"],
      "industry": "Financial Services",
      "industries": ["Fintech", "Payments"],
      "sub_industries": ["Payment Processing", "Financial Technology"],
      "description": "Online payment processing platform",
      "short_description": "Payment infrastructure for the internet",
      "founded_year": 2010,
      "employee_count": 8000,
      "employee_range": "5001-10000",
      "estimated_annual_revenue": 24000000000,
      "revenue_range": "$1B+",
      "funding_total": 2450000000,
      "funding_stage": "Series H",
      "investors": [
        "Sequoia Capital",
        "Andreessen Horowitz",
        "General Catalyst"
      ],
      "technologies": [
        "React",
        "Ruby on Rails",
        "AWS",
        "PostgreSQL"
      ],
      "keywords": ["payments", "fintech", "ecommerce"],
      "tags": ["unicorn", "b2b", "saas"],
      "linkedin_url": "https://linkedin.com/company/stripe",
      "twitter_url": "https://twitter.com/stripe",
      "facebook_url": "https://facebook.com/stripe",
      "crunchbase_url": "https://crunchbase.com/organization/stripe",
      "headquarters_location": {
        "city": "San Francisco",
        "state": "California",
        "country": "United States",
        "postal_code": "94105"
      },
      "locations": [
        {
          "city": "San Francisco",
          "state": "California",
          "country": "United States"
        },
        {
          "city": "Dublin",
          "country": "Ireland"
        }
      ],
      "phone_numbers": [
        {
          "raw_number": "+1-415-555-1234",
          "sanitized_number": "14155551234"
        }
      ],
      "social_media_urls": [
        "https://twitter.com/stripe",
        "https://linkedin.com/company/stripe"
      ],
      "blog_url": "https://stripe.com/blog",
      "news_articles": [
        {
          "title": "Stripe raises $600M",
          "url": "https://...",
          "published_date": "2023-03-15"
        }
      ],
      "competitors": [
        {
          "name": "PayPal",
          "id": "apollo_org_789"
        },
        {
          "name": "Square",
          "id": "apollo_org_101"
        }
      ],
      "similar_companies": [
        {
          "name": "Adyen",
          "id": "apollo_org_202"
        }
      ],
      "technologies_used": {
        "cms": ["Contentful"],
        "analytics": ["Google Analytics", "Mixpanel"],
        "hosting": ["AWS"],
        "payment": ["Stripe"]
      },
      "advertising_technologies": ["Google Ads"],
      "analytics_technologies": ["Google Analytics", "Segment"],
      "cms_technologies": ["Contentful"],
      "ecommerce_technologies": ["Shopify"],
      "hosting_technologies": ["AWS"],
      "marketing_technologies": ["HubSpot", "Marketo"],
      "payment_technologies": ["Stripe"],
      "seo_technologies": ["Moz"],
      "social_media_technologies": ["Twitter", "LinkedIn"],
      "last_updated": "2024-01-20T08:15:00Z",
      "created_at": "2010-01-01T00:00:00Z"
    }
  ]
}
```

### Apollo: Batch Process

**Limits**:
- **Batch Size**: Up to 50 records per request
- **Rate Limits**: Varies by plan (typically 100-1000 requests/minute)
- **Processing Time**: Usually 1-5 seconds for batch of 50

**Process Flow**:
1. **Submit Batch Request**: Send array of people/organizations
2. **Matching Phase**: Apollo matches each record against database
3. **Enrichment Phase**: Retrieves all available data for matches
4. **Response**: Returns enriched data + match status for each record

**Match Status Types**:
- **Full Match**: Complete profile found and returned
- **Partial Match**: Some data found, partial profile returned
- **Not Found**: No match in database

**Error Handling**:
- Invalid records are skipped (not returned)
- Valid records are still processed
- Response includes `errors` array for failed records

### Apollo: Additional Data Fields

When you enrich a lead in Apollo.io, you get **significantly more data** than basic contact info. Here's what's added:

#### For People (Beyond Email/Phone/Address):

**Professional Information** (10-15 fields):
- Job title, headline, summary
- Department, seniority level, functions
- Current company details
- Work experience (full history with dates, descriptions)
- Education history (schools, degrees, fields of study)
- Skills, languages, certifications
- Awards, publications, patents
- Inferred salary range
- Years of experience

**Social & Online Presence** (5-10 fields):
- LinkedIn profile URL
- Twitter, GitHub, Facebook URLs
- Personal website, blog URL
- Profile picture URL

**Company Context** (5-10 fields):
- Current company full profile
- Previous companies
- Company industry, size, revenue
- Company funding information
- Company technologies used

**Location & Demographics** (3-5 fields):
- Timezone
- Detailed location breakdown
- Inferred demographics

**Metadata** (3-5 fields):
- Apollo person ID
- Last updated timestamp
- Data source information
- Match confidence score

**Total Additional Fields**: **30-50+ fields per person**

#### For Organizations (Beyond Basic Company Info):

**Company Details** (15-20 fields):
- Full company description
- Industry, sub-industries
- Founded year
- Employee count and range
- Revenue estimates and ranges
- Funding total, stage, investors
- Technologies used (detailed breakdown)
- Keywords, tags

**Locations** (5-10 fields):
- Headquarters location
- All office locations
- Geographic presence

**Online Presence** (5-10 fields):
- All domains owned
- Social media profiles (LinkedIn, Twitter, Facebook)
- Crunchbase, AngelList URLs
- Blog URL

**Business Intelligence** (10-15 fields):
- Competitors list
- Similar companies
- News articles and recent news
- Technology stack breakdown by category
- Advertising, analytics, CMS, e-commerce tools
- Marketing, payment, SEO technologies

**Metadata** (3-5 fields):
- Apollo organization ID
- Last updated timestamp
- Creation date

**Total Additional Fields**: **40-60+ fields per organization**

---

## Hunter.io Enrichment

### Hunter: How It Works

Hunter.io's enrichment endpoint (`GET /enrichment`) takes minimal input (email, domain, name, or company) and returns all available information about a person or company from their database.

**Endpoint**: `GET /enrichment`

**How It Works**:
1. Provide one or more identifiers (email, domain, company name, first/last name)
2. Hunter matches against their database
3. Returns comprehensive profile with all available data
4. Works for both people and companies

**Request Examples**:
```
GET /enrichment?email=patrick@stripe.com
GET /enrichment?domain=stripe.com
GET /enrichment?company=Stripe
GET /enrichment?first_name=Patrick&last_name=Collison&domain=stripe.com
```

**Note**: Hunter.io does **not** have a dedicated batch enrichment endpoint like Apollo. However, you can:
- Make multiple parallel requests (respecting rate limits)
- Use their Lead Enrichment API (separate service) for bulk processing
- Use the `/leads` resource to manage enriched leads

### Hunter: Enrichment Process

**Single Request Process**:
1. **Input**: Email, domain, company name, or person name
2. **Matching**: Hunter finds matching records
3. **Enrichment**: Retrieves all available data
4. **Response**: Returns person and/or company data

**Lead Enrichment API** (Bulk Processing):
- Separate service for bulk enrichment
- Can process CSV files or API requests
- Returns enriched data with 100+ attributes

**Response Structure**:
```json
{
  "data": {
    "email": "patrick@stripe.com",
    "first_name": "Patrick",
    "last_name": "Collison",
    "full_name": "Patrick Collison",
    "position": "CEO",
    "company": "Stripe",
    "website": "stripe.com",
    "country": "United States",
    "city": "San Francisco",
    "state": "California",
    "zip": "94105",
    "phone_number": "+1-415-555-1234",
    "linkedin_url": "https://linkedin.com/in/patrickcollison",
    "twitter_url": "https://twitter.com/patrickc",
    "github_url": "https://github.com/patrickcollison",
    "facebook_url": "https://facebook.com/patrickcollison",
    "sources": [
      {
        "domain": "stripe.com",
        "uri": "https://stripe.com/about",
        "extracted_on": "2024-01-15",
        "still_on_page": true
      }
    ],
    "email_verification": {
      "result": "deliverable",
      "score": 95,
      "sources": [
        {
          "domain": "stripe.com",
          "uri": "https://stripe.com/team",
          "extracted_on": "2023-12-01"
        }
      ]
    },
    "company": {
      "name": "Stripe",
      "domain": "stripe.com",
      "industry": "Financial Services",
      "type": "Private",
      "size": "5001-10000",
      "employees": 8000,
      "revenue": 24000000000,
      "technologies": [
        {
          "name": "React",
          "category": "JavaScript Frameworks",
          "first_detected": "2018-05-15",
          "last_detected": "2024-01-20"
        },
        {
          "name": "AWS",
          "category": "Cloud Hosting",
          "first_detected": "2015-03-10",
          "last_detected": "2024-01-20"
        }
      ],
      "social_media": {
        "linkedin": "https://linkedin.com/company/stripe",
        "twitter": "https://twitter.com/stripe",
        "facebook": "https://facebook.com/stripe"
      },
      "locations": [
        {
          "city": "San Francisco",
          "state": "California",
          "country": "United States"
        }
      ]
    },
    "confidence_score": 98,
    "first_seen": "2015-06-15",
    "last_seen": "2024-01-20"
  },
  "meta": {
    "params": {
      "email": "patrick@stripe.com"
    }
  }
}
```

### Hunter: Additional Data Fields

When enriching with Hunter.io, you get these additional fields beyond basic contact info:

#### For People (Beyond Email/Phone/Address):

**Personal Information** (5-8 fields):
- Full name, first name, last name
- Position/job title
- Professional summary (if available)

**Social Media** (4-6 fields):
- LinkedIn profile URL
- Twitter, GitHub, Facebook URLs
- Profile verification status

**Company Context** (8-12 fields):
- Company name, domain, website
- Company industry, type, size
- Employee count, revenue estimates
- Company technologies used
- Company social media profiles
- Company locations

**Email Intelligence** (5-8 fields):
- Email verification result (deliverable/undeliverable/risky)
- Email confidence score (0-100)
- Email sources (where email was found)
- First seen date, last seen date
- Email pattern type
- MX records, SMTP information

**Data Quality** (3-5 fields):
- Overall confidence score
- Data sources with extraction dates
- Verification status
- Last updated timestamp

**Total Additional Fields**: **25-40+ fields per person**

#### For Companies (Beyond Basic Info):

**Company Details** (10-15 fields):
- Full company description
- Industry classification
- Company type (Private/Public)
- Employee count and size range
- Revenue estimates
- Founded year (if available)

**Technology Stack** (10-20 fields):
- All technologies used
- Technology categories
- First/last detected dates for each technology
- Technology paths/URLs

**Online Presence** (5-8 fields):
- All domains owned
- Social media profiles
- Website information

**Locations** (3-5 fields):
- Headquarters location
- Office locations
- Geographic presence

**Data Quality** (3-5 fields):
- Confidence scores
- Data sources
- Last updated timestamps

**Total Additional Fields**: **30-50+ fields per company**

---

## Data Comparison

### What You Start With:
- Email address
- Phone number
- Address (street, city, state, zip, country)

### What You Get After Enrichment:

#### Apollo.io Enrichment Adds:
- **30-50+ fields for people**
- **40-60+ fields for organizations**
- **Deep professional history** (work experience, education)
- **Social media profiles** (LinkedIn, Twitter, GitHub, etc.)
- **Company intelligence** (funding, competitors, technologies)
- **Inferred data** (salary ranges, experience years)
- **News and updates** (recent articles, company news)

#### Hunter.io Enrichment Adds:
- **25-40+ fields for people**
- **30-50+ fields for companies**
- **Email verification data** (deliverability, confidence scores)
- **Technology stack** (detailed breakdown)
- **Data sources** (where information was found)
- **Social media profiles**
- **Company intelligence** (revenue, employees, industry)

### Data Completeness Expectations:

**High Confidence Matches** (80-100%):
- **Apollo**: 80-95% of fields populated
- **Hunter**: 70-90% of fields populated

**Medium Confidence Matches** (50-79%):
- **Apollo**: 50-70% of fields populated
- **Hunter**: 40-60% of fields populated

**Low Confidence/Partial Matches** (20-49%):
- **Apollo**: 20-40% of fields populated
- **Hunter**: 15-30% of fields populated

**Not Found**:
- No additional data returned
- May return basic info if partial match exists

---

## Best Practices

### For Batch Enrichment:

1. **Batch Size Optimization**:
   - Apollo: Use full batch of 50 records when possible
   - Hunter: Process in parallel batches of 10-20 (respect rate limits)

2. **Input Data Quality**:
   - Provide as much input as possible (email + name + company)
   - Higher input quality = better matching = more enriched data

3. **Error Handling**:
   - Check match status for each record
   - Handle partial matches appropriately
   - Retry failed records separately

4. **Rate Limiting**:
   - Respect API rate limits
   - Implement exponential backoff for retries
   - Use batch endpoints to maximize efficiency

5. **Data Storage**:
   - Store enriched data with timestamps
   - Track data freshness (last_updated fields)
   - Re-enrich periodically (quarterly recommended)

6. **Cost Optimization**:
   - Use batch endpoints to reduce API calls
   - Cache enriched data to avoid re-enriching
   - Only enrich records that need updating

### Expected Data Volume:

**Before Enrichment** (Basic Lead):
- 4-6 fields: email, phone, address components

**After Apollo Enrichment**:
- **People**: 35-55 total fields (30-50 new fields)
- **Organizations**: 45-65 total fields (40-60 new fields)

**After Hunter Enrichment**:
- **People**: 30-45 total fields (25-40 new fields)
- **Companies**: 35-55 total fields (30-50 new fields)

**Combined (Both APIs)**:
- **People**: 50-70 total fields
- **Organizations**: 60-80 total fields

---

## Summary

### Apollo.io Batch Enrichment:
- **Process**: Send up to 50 records per batch request
- **Speed**: 1-5 seconds per batch
- **Additional Data**: 30-50+ fields for people, 40-60+ fields for organizations
- **Strengths**: Deep professional history, inferred data, company intelligence
- **Best For**: Comprehensive lead profiles, sales intelligence, B2B prospecting

### Hunter.io Enrichment:
- **Process**: Single requests or Lead Enrichment API for bulk
- **Speed**: 1-3 seconds per request
- **Additional Data**: 25-40+ fields for people, 30-50+ fields for companies
- **Strengths**: Email verification, technology stack, data source tracking
- **Best For**: Email-focused enrichment, technology intelligence, data quality

### Data Volume Increase:
- **Before**: 4-6 fields
- **After Apollo**: 35-65 fields (8-15x increase)
- **After Hunter**: 30-55 fields (7-12x increase)
- **After Both**: 50-80 fields (12-20x increase)

---

*Last Updated: Based on API documentation and best practices as of 2024*


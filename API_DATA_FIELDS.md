# Available Data Fields from APIs

This document lists all data fields/columns that can be returned by querying the APIs, excluding address, phone number, and email (which you already have).

---

## Hunter.io API

### Person/Contact Fields

- **first_name**: First name
- **last_name**: Last name
- **full_name**: Full name
- **position**: Job title/position
- **seniority**: Seniority level (e.g., "junior", "senior", "executive")
- **department**: Department name
- **company**: Company name
- **company_size**: Number of employees at company
- **website**: Company website/domain
- **linkedin_url**: LinkedIn profile URL
- **twitter_url**: Twitter profile URL
- **sources**: Array of sources where email was found
- **email_confidence_score**: Confidence score (0-100) for email accuracy
- **email_verification_result**: "deliverable", "undeliverable", "risky", "unknown"
- **email_verification_score**: Verification confidence score (0-100)
- **email_type**: Email pattern type (e.g., "firstname.lastname", "firstnamelastname")
- **email_pattern**: Detected email pattern
- **accept_all**: Whether domain accepts all emails (boolean)
- **disposable**: Whether email is disposable (boolean)
- **webmail**: Whether email is webmail (boolean)
- **mx_records**: MX records for domain
- **smtp_server**: SMTP server information
- **smtp_check**: SMTP check result

### Company/Organization Fields

- **domain**: Domain name
- **company_name**: Company name
- **industry**: Industry vertical
- **company_type**: Type of company
- **technologies**: Array of technologies used
- **social_media_urls**: Array of social media URLs
- **employee_count**: Number of employees
- **revenue**: Estimated revenue
- **headquarters_location**: Headquarters location details
- **country**: Country code
- **city**: City name
- **state**: State/region
- **zip**: ZIP/postal code
- **description**: Company description
- **founded_year**: Year company was founded
- **linkedin_url**: LinkedIn company page URL
- **twitter_url**: Twitter company profile URL
- **facebook_url**: Facebook page URL
- **instagram_url**: Instagram profile URL
- **youtube_url**: YouTube channel URL
- **github_url**: GitHub organization URL

### Email-Specific Fields

- **email_count**: Total number of emails found for domain
- **email_patterns**: Common email patterns used by company
- **email_verification_date**: Date email was verified
- **email_first_seen**: Date email was first detected
- **email_last_seen**: Date email was last detected

---

## Apollo.io API

### Person/Contact Fields

- **first_name**: First name
- **last_name**: Last name
- **full_name**: Full name
- **title**: Job title
- **headline**: Professional headline
- **summary**: Professional summary/bio
- **experience**: Array of work experience objects
  - `title`: Job title
  - `company`: Company name
  - `start_date`: Start date
  - `end_date`: End date (null if current)
  - `description`: Job description
- **education**: Array of education objects
  - `school`: School name
  - `degree`: Degree type
  - `field_of_study`: Field of study
  - `start_date`: Start date
  - `end_date`: End date
- **skills**: Array of skills
- **languages**: Array of languages spoken
- **certifications**: Array of certifications
- **awards**: Array of awards
- **publications**: Array of publications
- **patents**: Array of patents
- **interests**: Array of interests
- **person_id**: Apollo person ID
- **linkedin_url**: LinkedIn profile URL
- **twitter_url**: Twitter profile URL
- **github_url**: GitHub profile URL
- **facebook_url**: Facebook profile URL
- **personal_emails**: Array of personal email addresses (if different from work)
- **employment_history**: Detailed employment history
- **current_company**: Current company information
- **previous_companies**: Array of previous companies
- **seniority_level**: Seniority level
- **department**: Department name
- **subdepartments**: Sub-departments
- **functions**: Job functions
- **seniority**: Seniority classification
- **state**: State/region
- **city**: City name
- **country**: Country name
- **postal_code**: Postal/ZIP code
- **timezone**: Timezone
- **inferred_salary**: Estimated salary range
- **inferred_years_experience**: Years of experience
- **profile_picture_url**: Profile picture URL
- **website_url**: Personal website URL
- **blog_url**: Blog URL
- **industry**: Industry
- **keywords**: Keywords associated with person
- **tags**: Tags/categories
- **source**: Data source
- **last_updated**: Last update timestamp
- **created_at**: Creation timestamp

### Company/Organization Fields

- **organization_id**: Apollo organization ID
- **name**: Company name
- **website_url**: Company website
- **domain**: Primary domain
- **domains**: Array of all domains
- **industry**: Industry vertical
- **industries**: Array of industries
- **sub_industries**: Sub-industries
- **organization_keywords**: Keywords
- **description**: Company description
- **short_description**: Short description
- **founded_year**: Year founded
- **employee_count**: Number of employees
- **employee_range**: Employee range (e.g., "51-200")
- **estimated_annual_revenue**: Estimated annual revenue
- **revenue_range**: Revenue range
- **funding_total**: Total funding amount
- **funding_stage**: Funding stage
- **investors**: Array of investors
- **technologies**: Array of technologies used
- **keywords**: Keywords
- **tags**: Tags/categories
- **linkedin_url**: LinkedIn company page
- **twitter_url**: Twitter company profile
- **facebook_url**: Facebook page
- **crunchbase_url**: Crunchbase URL
- **angellist_url**: AngelList URL
- **tech_stack**: Technology stack details
- **headquarters_location**: Headquarters location object
  - `city`: City
  - `state`: State
  - `country`: Country
  - `postal_code`: Postal code
- **locations**: Array of office locations
- **phone_numbers**: Array of phone numbers (if different from main)
- **social_media_urls**: Array of social media URLs
- **blog_url**: Company blog URL
- **news_articles**: Array of news articles
- **recent_news**: Recent news articles
- **competitors**: Array of competitor companies
- **similar_companies**: Similar companies
- **technologies_used**: Detailed technology stack
- **advertising_technologies**: Advertising tech used
- **analytics_technologies**: Analytics tools used
- **cms_technologies**: CMS platforms used
- **ecommerce_technologies**: E-commerce platforms
- **hosting_technologies**: Hosting providers
- **marketing_technologies**: Marketing tools
- **payment_technologies**: Payment processors
- **seo_technologies**: SEO tools
- **social_media_technologies**: Social media platforms
- **last_updated**: Last update timestamp
- **created_at**: Creation timestamp

### Job Postings Fields

- **job_id**: Job posting ID
- **title**: Job title
- **description**: Job description
- **requirements**: Job requirements
- **location**: Job location
- **job_type**: Job type (full-time, part-time, contract)
- **posted_date**: Date posted
- **application_url**: Application URL
- **salary_range**: Salary range
- **experience_level**: Required experience level
- **skills_required**: Required skills
- **department**: Department
- **remote**: Whether job is remote (boolean)

### News Articles Fields

- **article_id**: Article ID
- **title**: Article title
- **url**: Article URL
- **published_date**: Publication date
- **author**: Author name
- **source**: News source
- **summary**: Article summary
- **content**: Article content
- **tags**: Article tags
- **related_organizations**: Related organizations
- **related_people**: Related people

---

## BuiltWith API

### Technology Stack Fields

- **domain**: Domain name
- **company_name**: Company name
- **technologies**: Array of technology objects
  - `name`: Technology name
  - `tag`: Technology tag/category
  - `first_detected`: First detection date
  - `last_detected`: Last detection date
  - `path`: Technology path/URL
  - `description`: Technology description
- **technology_categories**: Technology categories
  - `Analytics`: Analytics tools
  - `Advertising`: Advertising platforms
  - `CMS`: Content management systems
  - `Ecommerce`: E-commerce platforms
  - `Frameworks`: Web frameworks
  - `Hosting`: Hosting providers
  - `JavaScript`: JavaScript libraries
  - `Marketing`: Marketing tools
  - `Payment`: Payment processors
  - `Widgets`: Widgets and plugins
- **country**: Country code
- **city**: City name
- **state**: State/region
- **zip**: ZIP/postal code
- **employees**: Number of employees
- **vertical**: Industry vertical
- **followers**: Social media followers count
- **sku**: Product SKU count
- **spend**: Estimated technology spend
- **revenue**: Estimated revenue
- **pagerank**: Google PageRank
- **bwsrank**: BuiltWith rank
- **majesticrank**: Majestic rank
- **umbrellarank**: Umbrella rank
- **trancorank**: Tranco rank
- **social_urls**: Array of social media URLs
- **first_indexed**: First indexing date
- **last_indexed**: Last indexing date
- **technologies_count**: Total number of technologies detected
- **hosting_provider**: Web hosting provider
- **cdn_provider**: CDN provider
- **ssl_certificate**: SSL certificate information
- **cms_platform**: CMS platform used
- **ecommerce_platform**: E-commerce platform
- **payment_processors**: Array of payment processors
- **analytics_tools**: Array of analytics tools
- **advertising_platforms**: Array of advertising platforms
- **marketing_tools**: Array of marketing tools
- **framework**: Web framework
- **programming_language**: Programming language
- **server_location**: Server location
- **ip_address**: IP address
- **name_servers**: Name servers
- **mx_records**: MX records
- **related_domains**: Related domains (from relationships endpoint)
- **similar_technologies**: Similar technology stacks

### Dataset-Specific Fields

When using BuiltWith datasets, additional fields are available:
- **Domain**: Website domain
- **Country**: Country code
- **Spend**: Estimated spend
- **Revenue**: Estimated revenue
- **PageRank**: Google PageRank
- **BwsRank**: BuiltWith rank
- **MajesticRank**: Majestic rank
- **UmbrellaRank**: Umbrella rank
- **TrancoRank**: Tranco rank
- **Employees**: Number of employees
- **Vertical**: Industry vertical
- **Followers**: Social media followers
- **Sku**: Product SKU count
- **CompanyName**: Company name
- **Telephones**: Array of phone numbers
- **SocialUrls**: Array of social media URLs
- **City**: City name
- **State**: State/region
- **Zip**: ZIP/postal code
- **FirstIndexed**: First indexing timestamp
- **LastIndexed**: Last indexing timestamp
- **Techs**: Array of technology objects with detection dates

---

## Firecrawl API

### Scraped Content Fields

- **url**: Scraped URL
- **status_code**: HTTP status code
- **title**: Page title
- **description**: Meta description
- **markdown**: Markdown formatted content
- **html**: HTML content
- **raw_html**: Raw HTML source
- **text**: Plain text content
- **links**: Array of links found on page
- **images**: Array of images found on page
- **metadata**: Page metadata
  - `title`: Page title
  - `description`: Meta description
  - `keywords`: Meta keywords
  - `author`: Author
  - `og_title`: Open Graph title
  - `og_description`: Open Graph description
  - `og_image`: Open Graph image
  - `og_type`: Open Graph type
  - `twitter_card`: Twitter card type
  - `canonical_url`: Canonical URL
- **screenshot**: Screenshot (if requested)
- **sitemap**: Sitemap structure (from map endpoint)
- **extracted_data**: Structured data (from extract endpoint)
- **scraped_at**: Timestamp of scrape
- **content_length**: Content length
- **language**: Detected language
- **published_date**: Article published date (if detected)
- **author**: Article author (if detected)
- **headings**: Array of headings (h1, h2, h3, etc.)
- **paragraphs**: Array of paragraphs
- **lists**: Array of lists
- **tables**: Array of tables
- **code_blocks**: Array of code blocks
- **quotes**: Array of block quotes

### Crawl Job Fields

- **job_id**: Crawl job ID
- **status**: Job status ("running", "completed", "failed")
- **urls_scraped**: Number of URLs scraped
- **urls_total**: Total URLs to scrape
- **started_at**: Job start timestamp
- **completed_at**: Job completion timestamp
- **errors**: Array of errors encountered
- **results**: Array of scraped results

### Extract Fields (AI-Powered)

- **extracted_fields**: Structured data based on schema/prompt
- **confidence_score**: Extraction confidence score
- **extraction_method**: Method used ("llm-extract" or "schema")
- **raw_content**: Raw content used for extraction
- **validation_status**: Data validation status

---

## ScrapingBee API

### Scraped Content Fields

- **url**: Scraped URL
- **status_code**: HTTP status code
- **body**: HTML body content
- **headers**: Response headers
- **title**: Page title
- **screenshot**: Screenshot image (base64 encoded, if requested)
- **pdf**: PDF content (if pdf=true)
- **markdown**: Markdown formatted content (if return_page_markdown=true)
- **text**: Plain text content (if return_page_text=true)
- **extracted_data**: Extracted data (if extract_rules provided)
- **page_source**: Page source HTML (if return_page_source=true)
- **final_url**: Final URL after redirects
- **redirect_count**: Number of redirects
- **load_time**: Page load time in milliseconds
- **content_type**: Content type
- **content_length**: Content length
- **encoding**: Character encoding
- **language**: Detected language
- **meta_tags**: Meta tags
- **links**: Array of links
- **images**: Array of images
- **scripts**: Array of scripts
- **stylesheets**: Array of stylesheets
- **forms**: Array of forms
- **tables**: Array of tables

### Screenshot Fields

- **screenshot**: Base64 encoded screenshot image
- **screenshot_width**: Screenshot width
- **screenshot_height**: Screenshot height
- **screenshot_format**: Image format (PNG, JPEG)
- **screenshot_selector**: CSS selector used (if screenshot_selector provided)
- **screenshot_full_page**: Whether full page screenshot (boolean)

### PDF Fields

- **pdf**: PDF file content (base64 encoded)
- **pdf_size**: PDF file size
- **pdf_pages**: Number of pages
- **pdf_format**: PDF format version

### Extracted Data Fields (with extract_rules)

When using `extract_rules` or `ai_extract_rules`, you can extract:
- **Any custom field**: Based on your extraction rules
- **title**: Page title
- **headings**: All headings
- **paragraphs**: All paragraphs
- **links**: All links with text and URLs
- **images**: All images with alt text and URLs
- **metadata**: Meta tags
- **structured_data**: JSON-LD structured data
- **open_graph**: Open Graph tags
- **twitter_card**: Twitter Card tags
- **schema_org**: Schema.org markup

### AI Extraction Fields (Beta)

When using `ai_query` or `ai_extract_rules`:
- **ai_extracted_data**: AI-extracted structured data
- **extraction_confidence**: Confidence score
- **extraction_method**: AI method used
- **extracted_fields**: Fields extracted based on query

---

## Summary by Category

### Personal/Contact Information
- First name, last name, full name
- Job title, position, headline
- Department, seniority level
- Professional summary/bio
- LinkedIn, Twitter, GitHub, Facebook URLs
- Profile picture URL
- Personal website URL
- Skills, languages, certifications
- Work experience, education history
- Interests, awards, publications

### Company/Organization Information
- Company name, domain, website
- Industry, sub-industries
- Employee count, revenue estimates
- Founded year, funding information
- Company description
- Headquarters and office locations
- Social media URLs
- Technology stack
- Competitors, similar companies
- News articles, recent news

### Technology Stack
- Technologies used (CMS, frameworks, hosting, etc.)
- Technology categories
- First/last detected dates
- Hosting provider, CDN provider
- SSL certificate information
- Server location, IP address
- Analytics tools, advertising platforms
- Payment processors, marketing tools

### Web Content
- Page title, description, metadata
- HTML, Markdown, plain text content
- Links, images, scripts, stylesheets
- Headings, paragraphs, tables
- Screenshots, PDFs
- Structured data (JSON-LD, Schema.org)
- Open Graph, Twitter Card tags
- Published date, author
- Language, encoding

### Rankings & Metrics
- PageRank, various ranking metrics
- Employee count ranges
- Revenue estimates
- Technology spend estimates
- Social media followers
- Product SKU counts

### Timestamps
- First/last indexed dates
- First/last detected dates
- Created at, last updated
- Published dates
- Job posting dates

---

## Notes

1. **Not all fields are available for every record** - Some fields may be null or empty depending on data availability.

2. **Field availability varies by API tier** - Some fields may only be available on premium/paid plans.

3. **Data freshness** - Timestamps indicate when data was last updated, which helps assess data recency.

4. **Combining APIs** - You can combine data from multiple APIs to get a more complete picture. For example:
   - Use Hunter.io for email verification
   - Use Apollo.io for detailed person/company profiles
   - Use BuiltWith for technology stack
   - Use Firecrawl/ScrapingBee for web content extraction

5. **Custom extraction** - Firecrawl and ScrapingBee allow custom extraction rules, so you can extract any field that exists on a webpage.

---

*Last Updated: Based on API documentation as of 2024*


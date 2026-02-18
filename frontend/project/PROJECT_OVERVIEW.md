# Lead Packs Frontend

A clean, professional Next.js frontend for an AI-powered lead generation system.

## Overview

This application provides a user-friendly interface for:
1. Learning about the Lead Packs product
2. Configuring and generating custom lead packs
3. Processing payments via Stripe
4. Downloading lead data in CSV or JSONL format

## Tech Stack

- **Framework**: Next.js 13 (App Router)
- **Styling**: Tailwind CSS + shadcn/ui components
- **Language**: TypeScript
- **Icons**: Lucide React

## Project Structure

```
app/
├── page.tsx              # Landing page (/)
├── generate/
│   └── page.tsx          # Pack generator (/generate)
├── success/
│   └── page.tsx          # Post-checkout success (/success)
└── layout.tsx            # Root layout

components/
├── ui/                   # shadcn/ui components
├── error-banner.tsx      # Error message display
├── feature-card.tsx      # Feature highlights
├── form-card.tsx         # Form container
└── preview-card.tsx      # Preview container

lib/
├── api.ts                # Backend API integration
├── config.ts             # Environment configuration
└── utils.ts              # Utility functions
```

## Environment Variables

Create a `.env.local` file with:

```env
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
```

## Backend Integration

The frontend communicates with a FastAPI backend via two main endpoints:

### POST /start-pack
Creates a Stripe Checkout Session and initiates pack generation.

**Request:**
```json
{
  "query": "restaurants in Boca Raton, FL",
  "country": "United States",
  "state": "Florida",
  "county": null,
  "city": "Boca Raton",
  "niche": "restaurants",
  "limit": 50
}
```

**Response:**
```json
{
  "checkout_url": "https://checkout.stripe.com/...",
  "pack_id": "pack_xyz123"
}
```

### GET /download-pack
Downloads the generated lead pack.

**Query Parameters:**
- `session_id`: Stripe checkout session ID
- `format`: `csv` or `jsonl`

**Response:** File download stream

## User Flow

1. **Landing Page** (`/`)
   - Hero section with product explanation
   - Feature cards highlighting key benefits
   - 3-step process overview
   - CTA buttons to generate page

2. **Generate Page** (`/generate`)
   - Left side: Configuration form
     - Country, State, County, City inputs
     - Niche selection (preset + custom)
     - Lead count selector
     - Real-time query preview
   - Right side: Pack summary preview
     - Location breakdown
     - Niche and lead count
     - Query display
     - Usage tips
   - On submit:
     - Calls `/start-pack` endpoint
     - Redirects to Stripe Checkout

3. **Success Page** (`/success`)
   - Reads `session_id` from URL
   - Displays success message
   - Provides download buttons for CSV/JSONL
   - Links back to home or generate page

## Key Features

### Responsive Design
- Mobile-first approach
- Side-by-side layout on desktop
- Stacked layout on mobile

### Real-time Updates
- Query preview updates as user types
- Pack summary dynamically reflects form state
- Form validation with disabled states

### Error Handling
- Clear error messages for API failures
- Missing session handling on success page
- Form validation feedback

### Loading States
- Spinner during checkout redirect
- Disabled buttons during submission
- Clear feedback for all async operations

## Development

```bash
# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build

# Start production server
npm start
```

## Extending the Frontend

### Adding New Niches
Update the `NICHES` array in `app/generate/page.tsx`:

```typescript
const NICHES = [
  'Restaurants',
  'Nail Salons',
  // Add more here
  'Custom',
];
```

### Modifying Lead Counts
Update the `LEAD_COUNTS` array in `app/generate/page.tsx`:

```typescript
const LEAD_COUNTS = [20, 50, 100, 200, 500];
```

### Customizing Styling
All components use Tailwind CSS classes. Theme colors can be modified in `app/globals.css` and `tailwind.config.ts`.

### Adding Analytics
Add tracking to key user actions:
- Pack generation button clicks
- Successful checkout redirects
- Download button clicks

## API Helper Functions

All backend communication is centralized in `lib/api.ts`:

- `startPack()`: Initiates pack generation and checkout
- `getDownloadUrl()`: Constructs download URLs

This makes it easy to:
- Mock API calls for testing
- Add authentication headers
- Implement retry logic
- Switch backend URLs

## Notes

- The frontend uses static export (`output: 'export'` in `next.config.js`)
- All pages are client-side rendered for interactivity
- Backend URL is configurable via environment variables
- Stripe handles all payment processing
- No sensitive data is stored in the frontend

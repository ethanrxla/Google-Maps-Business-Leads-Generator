'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { FormCard } from '@/components/form-card';
import { PreviewCard } from '@/components/preview-card';
import { ErrorBanner } from '@/components/error-banner';
import { startPack } from '@/lib/api';
import { Loader2, ArrowLeft } from 'lucide-react';
import Link from 'next/link';
import { LEAD_PACK_SIZES, LEAD_PACK_PRICES, formatLeadOption } from '@/lib/lead_sizes';

const NICHES = [
  'Restaurants',
  'Nail Salons',
  'Hair Salons',
  'Medical Spas',
  'Gyms & Fitness Centers',
  'Dental Offices',
  'Real Estate Agencies',
  'Auto Repair Shops',
  'Coffee Shops',
  'Custom',
];

export default function GeneratePage() {
  const [country, setCountry] = useState('United States');
  const [state, setState] = useState('');
  const [county, setCounty] = useState('');
  const [city, setCity] = useState('');
  const [niche, setNiche] = useState('');
  const [customNiche, setCustomNiche] = useState('');
  const [leadCount, setLeadCount] = useState<number>(LEAD_PACK_SIZES[0]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const actualNiche = niche === 'Custom' ? customNiche : niche;

  const generateQuery = () => {
    if (!actualNiche || !city) return '';

    if (state) {
      return `${actualNiche} in ${city}, ${state}`;
    }

    if (country) {
      return `${actualNiche} in ${city}, ${country}`;
    }

    return `${actualNiche} in ${city}`;
  };

  const query = generateQuery();

  const isFormValid = Boolean(city && actualNiche && leadCount > 0);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!isFormValid) return;

    setIsSubmitting(true);
    setError(null);

    try {
      const response = await startPack({
        query,
        country: country || null,
        state: state || null,
        county: county || null,
        city,
        niche: actualNiche || null,
        limit: leadCount,
      });

      window.location.href = response.checkout_url;
    } catch (err: any) {
      console.error('Error starting pack:', err);
      setError(err?.message || 'Something went wrong starting your pack. Please try again.');
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        <div className="mb-8">
          <Link href="/">
            <Button variant="ghost" size="sm">
              <ArrowLeft className="mr-2 h-4 w-4" />
              Back to Home
            </Button>
          </Link>
        </div>

        <div className="mb-8 text-center">
          <h1 className="mb-2 text-3xl font-bold sm:text-4xl">
            Generate Your Lead Pack
          </h1>
          <p className="text-muted-foreground">
            Configure your search parameters to get targeted leads for your business
          </p>
        </div>

        <div className="grid gap-8 lg:grid-cols-2">
          <FormCard>
            <h2 className="mb-6 text-xl font-semibold">Pack Configuration</h2>

            {error && (
              <ErrorBanner
                message={error}
                onDismiss={() => setError(null)}
                className="mb-6"
              />
            )}

            <form onSubmit={handleSubmit} className="space-y-6">
              <div className="space-y-2">
                <Label htmlFor="country">Country</Label>
                <Input
                  id="country"
                  value={country}
                  onChange={(e) => setCountry(e.target.value)}
                  placeholder="e.g., United States"
                />
              </div>

              <div className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="state">State / Region</Label>
                  <Input
                    id="state"
                    value={state}
                    onChange={(e) => setState(e.target.value)}
                    placeholder="e.g., Florida"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="county">County (Optional)</Label>
                  <Input
                    id="county"
                    value={county}
                    onChange={(e) => setCounty(e.target.value)}
                    placeholder="e.g., Palm Beach"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="city">City *</Label>
                <Input
                  id="city"
                  value={city}
                  onChange={(e) => setCity(e.target.value)}
                  placeholder="e.g., Boca Raton"
                  required
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="niche">Niche *</Label>
                <Select value={niche} onValueChange={setNiche}>
                  <SelectTrigger id="niche">
                    <SelectValue placeholder="Select a niche" />
                  </SelectTrigger>
                  <SelectContent>
                    {NICHES.map((n) => (
                      <SelectItem key={n} value={n}>
                        {n}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {niche === 'Custom' && (
                <div className="space-y-2">
                  <Label htmlFor="customNiche">Custom Niche *</Label>
                  <Input
                    id="customNiche"
                    value={customNiche}
                    onChange={(e) => setCustomNiche(e.target.value)}
                    placeholder="e.g., Italian restaurants"
                    required
                  />
                  <p className="text-xs text-muted-foreground">
                    Use specific niches for higher quality results
                  </p>
                </div>
              )}

              <div className="space-y-2">
                <Label htmlFor="leadCount">Number of Leads</Label>
                <Select value={String(leadCount)} onValueChange={(v) => setLeadCount(Number(v))}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select lead count" />
                  </SelectTrigger>
                  <SelectContent>
                    {LEAD_PACK_SIZES.map((size) => (
                      <SelectItem key={size} value={String(size)}>
                        {formatLeadOption(size)}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <p className="text-xs text-muted-foreground">
                  Raw lead packs only. Price: ${LEAD_PACK_PRICES[leadCount] || '-'}
                </p>
              </div>

              <div className="space-y-2">
                <Label htmlFor="queryPreview">Search Query Preview</Label>
                <Input
                  id="queryPreview"
                  value={query || 'Configure fields above to see query'}
                  readOnly
                  className="bg-muted"
                />
                <p className="text-xs text-muted-foreground">
                  This is the search query we will use to find leads
                </p>
              </div>

              <Button
                type="submit"
                className="w-full"
                size="lg"
                disabled={!isFormValid || isSubmitting}
              >
                {isSubmitting ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Processing...
                  </>
                ) : (
                  'Continue to Checkout'
                )}
              </Button>
            </form>
          </FormCard>

          <div className="lg:sticky lg:top-8 lg:self-start">
            <PreviewCard>
              <h2 className="mb-6 text-xl font-semibold">Pack Summary</h2>

              <div className="space-y-4">
                <div>
                  <h3 className="mb-1 text-sm font-medium text-muted-foreground">
                    Location
                  </h3>
                  <p className="text-base">
                    {city || 'Not specified'}
                    {state && `, ${state}`}
                    {country && ` - ${country}`}
                  </p>
                </div>

                <div>
                  <h3 className="mb-1 text-sm font-medium text-muted-foreground">
                    Niche
                  </h3>
                  <p className="text-base">
                    {actualNiche || 'Not specified'}
                  </p>
                </div>

                <div>
                  <h3 className="mb-1 text-sm font-medium text-muted-foreground">
                    Approximate Leads
                  </h3>
                  <p className="text-base">
                    {leadCount} leads • ${LEAD_PACK_PRICES[leadCount] || '-'}
                  </p>
                </div>

                <div className="rounded-lg border bg-background p-4">
                  <h3 className="mb-2 text-sm font-medium">Search Query</h3>
                  <p className="text-sm text-muted-foreground">
                    {query || 'Configure the form to generate a query'}
                  </p>
                </div>

                <div className="rounded-lg border-l-4 border-primary bg-primary/5 p-4">
                  <h3 className="mb-2 text-sm font-semibold">Tips</h3>
                  <ul className="space-y-1 text-sm text-muted-foreground">
                    <li>• Use specific niches for better results</li>
                    <li>• Example: Italian restaurants vs restaurants</li>
                    <li>• Include state for more accurate targeting</li>
                  </ul>
                </div>
              </div>
            </PreviewCard>
          </div>
        </div>
      </div>
    </div>
  );
}

'use client';

import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { FeatureCard } from '@/components/feature-card';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { MapPin, Target, Sparkles, Download, ArrowRight } from 'lucide-react';
import Image from 'next/image';
import { FEATURED_PACKS, PackColorVariant } from '@/lib/featured-packs';
import { useEffect, useState } from 'react';
import {
  Carousel,
  CarouselContent,
  CarouselItem,
  CarouselNext,
  CarouselPrevious,
} from '@/components/ui/carousel';
import { BACKEND_URL } from '@/lib/config';
import { RetroHeader, RetroShell } from '@/components/RetroShell';
import { startFeaturedPack } from '@/lib/api';
import { track } from '@/lib/analytics';
import { LEAD_PACK_SIZES, LEAD_PACK_PRICES, formatLeadOption } from '@/lib/lead_sizes';

const colorClasses: Record<PackColorVariant, string> = {
  orange: 'border-orange-200 bg-orange-50 text-orange-900 dark:border-orange-900/40 dark:bg-orange-950/30',
  pink: 'border-pink-200 bg-pink-50 text-pink-900 dark:border-pink-900/40 dark:bg-pink-950/30',
  green: 'border-emerald-200 bg-emerald-50 text-emerald-900 dark:border-emerald-900/40 dark:bg-emerald-950/30',
  blue: 'border-blue-200 bg-blue-50 text-blue-900 dark:border-blue-900/40 dark:bg-blue-950/30',
  gray: 'border-slate-200 bg-slate-50 text-slate-900 dark:border-slate-800 dark:bg-slate-950/40',
};

export default function Home() {
  const [loadingId, setLoadingId] = useState<string | null>(null);
  const [errorId, setErrorId] = useState<string | null>(null);
  const [domain, setDomain] = useState('');
  const [scanResult, setScanResult] = useState<any | null>(null);
  const [scanError, setScanError] = useState<string | null>(null);
  const [scanLoading, setScanLoading] = useState(false);
  const [selectedSize, setSelectedSize] = useState<Record<string, number>>({});

  useEffect(() => {
    track('page_view', { page: 'home' });
  }, []);

  const handleFeaturedPurchase = async (packId: string) => {
    const pack = FEATURED_PACKS.find((p) => p.id === packId);
    if (!pack) return;
    const size = selectedSize[packId] ?? LEAD_PACK_SIZES[0];
    setLoadingId(`${packId}-basic_pack`);
    setErrorId(null);
    try {
      track('stripe_checkout_started', { pack_id: packId, product_type: 'basic_pack', lead_count: size });
      const res = await startFeaturedPack(pack, 'basic_pack', size);
      window.location.href = res.checkout_url;
    } catch (err) {
      console.error(err);
      setErrorId(`${packId}-basic_pack`);
      setLoadingId(null);
    }
  };

  const handleDomainScan = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setScanError(null);
    setScanResult(null);
    if (!domain.trim()) {
      setScanError('Please enter a domain to scan.');
      return;
    }
    setScanLoading(true);
    track('domain_scan_started', { domain });
    try {
      const res = await fetch(`${BACKEND_URL}/harvest-domain`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ domain: domain.trim(), sources: ['duckduckgo', 'crtsh', 'github', 'virustotal', 'netlas','yahoo','baidu','linkedin','censys','dnsdumpster','hackertarget','hunter','shodan','threatcrowd','urlscan'], limit: 50 }),
      });
      let data: any = null;
      try {
        data = await res.json();
      } catch (jsonErr) {
        console.error('harvest-domain json parse failed', jsonErr);
        throw jsonErr;
      }
      setScanResult(data);
      track('domain_scan_completed', { domain, status: data.status });
    } catch (err) {
      console.error(err);
      setScanError('Unable to run the scan right now.');
      track('domain_scan_failed', { domain });
    } finally {
      setScanLoading(false);
    }
  };

  return (
    <RetroShell>
      <RetroHeader />
      <main className="relative">
        <div className="pointer-events-none absolute inset-0 -z-0 overflow-hidden">
          <div className="absolute left-6 top-20 h-40 w-40 opacity-50 sm:h-56 sm:w-56">
            <Image src="/retro/data-ryan.gif" alt="retro data" fill className="object-contain" />
          </div>
          <div className="absolute right-10 bottom-20 h-32 w-32 opacity-50 sm:h-48 sm:w-48">
            <Image src="/retro/cookie.gif" alt="retro cookie" fill className="object-contain" />
          </div>
        </div>
        <div className="mx-auto max-w-7xl px-4 py-16 sm:px-6 lg:px-8">
          <section className="relative overflow-hidden rounded-xl border-2 border-yellow-200/70 bg-gradient-to-r from-white/85 to-cyan-50/85 p-8 shadow-[0_0_30px_rgba(255,255,255,0.35)] backdrop-blur">
            <div className="pointer-events-none absolute -left-10 top-0 hidden h-48 w-48 sm:block md:h-64 md:w-64">
              <Image src="/retro/data.gif" alt="data animation" fill className="object-contain opacity-70" />
            </div>
            <div className="pointer-events-none absolute -right-10 -bottom-12 hidden h-48 w-48 sm:block md:h-64 md:w-64">
              <Image src="/retro/data-numbers.gif" alt="numbers animation" fill className="object-contain opacity-70" />
            </div>
            <div className="mx-auto max-w-3xl text-center">
              <p className="mb-2 text-xs uppercase tracking-[0.25em] text-purple-600">Lead Store 2004</p>
              <h1 className="mb-6 text-4xl font-black uppercase tracking-tight text-black drop-shadow-[2px_2px_0px_rgba(255,255,255,0.6)] sm:text-5xl lg:text-6xl">
                Instant Local Lead Packs
              </h1>
              <p className="mb-8 text-lg text-slate-700 sm:text-xl">
                Local niche packs (20 leads) with Standard or Enriched tiers, plus single-domain OSINT scans when you need deeper intel.
              </p>
              <div className="flex flex-col items-center justify-center gap-4 sm:flex-row">
                <Link href="/generate">
                  <Button size="lg" className="w-full border-2 border-yellow-300 bg-gradient-to-r from-amber-400 to-orange-500 text-black shadow-[0_0_18px_rgba(255,200,0,0.6)] sm:w-auto">
                    Generate a Lead Pack
                    <ArrowRight className="ml-2 h-4 w-4" />
                  </Button>
                </Link>
                <Link href="/generate">
                  <Button size="lg" variant="outline" className="w-full border-2 border-cyan-400 bg-white/70 text-cyan-700 shadow-[0_0_12px_rgba(0,200,255,0.4)] sm:w-auto">
                    Learn More
                  </Button>
                </Link>
              </div>
            </div>
          </section>

          <section className="mt-24 rounded-xl border-2 border-fuchsia-200/70 bg-white/90 p-8 shadow-[0_0_25px_rgba(255,0,150,0.25)] backdrop-blur">
            <h2 className="mb-12 text-center text-3xl font-black uppercase tracking-[0.12em] text-fuchsia-700">
              Why Choose Lead Packs?
            </h2>
            <div className="grid gap-8 sm:grid-cols-2 lg:grid-cols-4">
              <FeatureCard
                icon={MapPin}
                title="Location-Based"
                description="Target leads by city, state, county, or country. Get hyper-local results for your business needs."
              />
              <FeatureCard
                icon={Target}
                title="Niche & Keyword Driven"
                description="Filter by specific industries like restaurants, salons, gyms, or any niche you need."
              />
              <FeatureCard
                icon={Sparkles}
                title="AI-Enriched Data"
                description="Every lead includes phone numbers, emails, quality scores, and AI-generated outreach copy."
              />
              <FeatureCard
                icon={Download}
                title="Instant Download"
                description="Get your leads immediately after payment in CSV or JSONL format, ready to use."
              />
            </div>
          </section>

          <section className="mt-24 rounded-xl border-4 border-cyan-200/80 bg-white/90 p-6 shadow-[0_0_25px_rgba(0,200,255,0.35)] backdrop-blur">
            <div className="mb-6 text-center">
              <h2 className="text-3xl font-black uppercase tracking-[0.16em] text-cyan-700">Featured Lead Packs</h2>
              <p className="text-muted-foreground">
                Pre-built AI-enriched packs ready to buy instantly. Choose Standard or Enriched (20 leads per pack).
              </p>
            </div>
            <Carousel className="w-full">
              <CarouselContent>
                {FEATURED_PACKS.map((pack, idx) => {
                  const colorClass = colorClasses[pack.color] || colorClasses.gray;
                  return (
                    <CarouselItem
                      key={`${pack.id}-${idx}`}
                      className="basis-full sm:basis-1/2 lg:basis-1/3 xl:basis-1/4"
                    >
                      <Card className={`overflow-hidden border ${colorClass} shadow-[0_10px_25px_rgba(0,0,0,0.12)]`}>
                        <div className="relative h-40 w-full">
                          <Image
                            src="/lead-pack-thumbnail.jpg"
                            alt={`${pack.title} thumbnail`}
                            fill
                            className="object-cover"
                            sizes="(max-width: 768px) 100vw, 33vw"
                          />
                        </div>
                        <CardHeader className="space-y-1">
                          <CardTitle className="text-lg uppercase tracking-wide">{pack.title}</CardTitle>
                          <p className="text-sm text-muted-foreground capitalize">{pack.niche}</p>
                        </CardHeader>
                        <CardContent className="space-y-3 text-sm">
                          <div className="flex flex-wrap gap-2 text-muted-foreground">
                            <span>{pack.city}, {pack.state}</span>
                            <span>• {pack.country}</span>
                          </div>
                          <div className="space-y-2 text-sm">
                            <div className="rounded-md border-2 border-yellow-200 bg-gradient-to-r from-yellow-50 to-white px-3 py-2 shadow-inner">
                              <div className="flex items-center justify-between">
                                <span className="font-semibold">Raw Leads</span>
                                <span className="text-muted-foreground">
                                  ${LEAD_PACK_PRICES[selectedSize[pack.id] ?? LEAD_PACK_SIZES[0]]}
                                </span>
                              </div>
                              <p className="text-xs text-muted-foreground">Choose a pack size of raw leads.</p>
                              <select
                                className="mt-2 w-full rounded-md border px-2 py-2 text-sm"
                                value={selectedSize[pack.id] ?? LEAD_PACK_SIZES[0]}
                                onChange={(e) =>
                                  setSelectedSize((prev) => ({
                                    ...prev,
                                    [pack.id]: Number(e.target.value),
                                  }))
                                }
                              >
                                {LEAD_PACK_SIZES.map((size) => (
                                  <option key={size} value={size}>
                                    {formatLeadOption(size)}
                                  </option>
                                ))}
                              </select>
                              <Button
                                className="mt-2 w-full"
                                onClick={() => handleFeaturedPurchase(pack.id)}
                                disabled={loadingId === `${pack.id}-basic_pack`}
                              >
                                {loadingId === `${pack.id}-basic_pack` ? 'Redirecting...' : 'Buy Now'}
                              </Button>
                            </div>
                          </div>
                          {errorId === `${pack.id}-basic_pack` ? (
                            <p className="text-xs text-destructive">Unable to start checkout. Try again.</p>
                          ) : null}
                        </CardContent>
                      </Card>
                    </CarouselItem>
                  );
                })}
              </CarouselContent>
              <CarouselPrevious />
              <CarouselNext />
            </Carousel>
          </section>

          <section className="mt-24 rounded-xl border-4 border-green-200/70 bg-white/90 p-8 shadow-[0_0_25px_rgba(0,200,120,0.35)] backdrop-blur">
            <div className="mx-auto max-w-5xl grid gap-6 lg:grid-cols-[1.1fr_0.9fr] items-center">
              <div>
                <h2 className="text-3xl font-black uppercase tracking-[0.14em] text-green-700">Single-Domain OSINT Scan ($7)</h2>
                <p className="mt-2 text-muted-foreground">
                  Run a lightweight theHarvester scan to find public emails and hosts for a domain.
                </p>
                <form className="mt-6 flex flex-col gap-3 sm:flex-row" onSubmit={handleDomainScan}>
                  <input
                    value={domain}
                    onChange={(e) => setDomain(e.target.value)}
                    className="flex-1 rounded-md border-2 border-green-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-400"
                    placeholder="example.com"
                  />
                  <Button type="submit" disabled={scanLoading} className="border-2 border-green-300 bg-gradient-to-r from-green-400 to-emerald-500 text-white shadow-[0_0_16px_rgba(0,200,120,0.4)]">
                    {scanLoading ? 'Scanning...' : 'Scan this domain'}
                  </Button>
                </form>
                {scanError && <p className="mt-2 text-sm text-destructive">{scanError}</p>}
                {scanResult && (
                  <div className="mt-6 rounded-md border bg-muted/50 p-4 text-sm">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="font-semibold">{scanResult.domain}</p>
                        <p className="text-muted-foreground">Status: {scanResult.status}</p>
                      </div>
                      <div className="text-right text-muted-foreground">
                        <p>Sources: {(scanResult.sources || []).join(', ')}</p>
                        <p>Lines: {scanResult.lines_in_raw ?? 0}</p>
                      </div>
                    </div>
                    {scanResult.checkout_url && (
                      <div className="mt-3 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                        <p className="font-semibold text-green-700">Ready to download your scan?</p>
                        <Button
                          onClick={() => (window.location.href = scanResult.checkout_url)}
                          className="border-2 border-green-300 bg-gradient-to-r from-green-400 to-emerald-500 text-white shadow-[0_0_16px_rgba(0,200,120,0.4)]"
                        >
                          Purchase &amp; Download
                        </Button>
                      </div>
                    )}
                    {scanResult.emails && Array.isArray(scanResult.emails) && (
                      <div className="mt-3">
                        <p className="font-semibold">Emails Found</p>
                        <ul className="list-disc space-y-1 pl-4">
                          {scanResult.emails.map((e: string) => (
                            <li key={e}>{e}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                    {scanResult.hosts && Array.isArray(scanResult.hosts) && (
                      <div className="mt-3">
                        <p className="font-semibold">Hosts</p>
                        <ul className="list-disc space-y-1 pl-4">
                          {scanResult.hosts.map((h: string) => (
                            <li key={h}>{h}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                )}
              </div>
              <div className="relative h-72 w-full overflow-hidden rounded-lg border-2 border-green-200 shadow-[0_0_18px_rgba(0,200,120,0.35)] sm:h-80">
                <Image
                  src="/58878FC7-07E1-417D-A794-D312BA8BD5F6.jpg"
                  alt="Domain scan product"
                  fill
                  sizes="(max-width: 768px) 100vw, 50vw"
                  className="object-cover"
                />
              </div>
            </div>
          </section>

          <section className="mt-24 rounded-xl border-4 border-amber-200/70 bg-white/90 p-8 shadow-[0_0_25px_rgba(255,200,0,0.35)] backdrop-blur">
              <div className="relative mx-auto max-w-3xl">
              <h2 className="mb-8 text-center text-3xl font-black uppercase tracking-[0.14em] text-amber-700">
                How It Works
              </h2>
              <div className="space-y-6">
                <div className="flex gap-4">
                  <div className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-full bg-primary text-lg font-bold text-primary-foreground">
                    1
                  </div>
                  <div>
                    <h3 className="mb-1 text-lg font-semibold">
                      Pick Your Pack
                    </h3>
                    <p className="text-muted-foreground">
                      Choose Standard ($12) or Enriched ($24) 20-lead packs for your city and niche. We handle the search and enrichment.
                    </p>
                  </div>
                </div>
                <div className="flex gap-4">
                  <div className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-full bg-primary text-lg font-bold text-primary-foreground">
                    2
                  </div>
                  <div>
                    <h3 className="mb-1 text-lg font-semibold">
                      Optional OSINT Scan
                    </h3>
                    <p className="text-muted-foreground">
                      Need deeper intel on a single domain? Run a quick OSINT scan to pull public emails and hosts.
                    </p>
                  </div>
                </div>
                <div className="flex gap-4">
                  <div className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-full bg-primary text-lg font-bold text-primary-foreground">
                    3
                  </div>
                  <div>
                    <h3 className="mb-1 text-lg font-semibold">
                      Secure Checkout
                    </h3>
                    <p className="text-muted-foreground">
                      Pay via Stripe (card) or crypto checkout, then get instant access to your pack or scan results.
                    </p>
                  </div>
                </div>
                <div className="flex gap-4">
                  <div className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-full bg-primary text-lg font-bold text-primary-foreground">
                    4
                  </div>
                  <div>
                    <h3 className="mb-1 text-lg font-semibold">
                      Download & Use
                    </h3>
                    <p className="text-muted-foreground">
                      Download CSV or JSONL instantly and start outreach with phone, email, scores, and AI copy included.
                    </p>
                  </div>
                </div>
              </div>
              <div className="mt-8 text-center">
                <Link href="/generate">
                  <Button size="lg" className="border-2 border-amber-300 bg-gradient-to-r from-amber-400 to-orange-400 text-black shadow-[0_0_18px_rgba(255,200,0,0.5)]">
                    Get Started Now
                    <ArrowRight className="ml-2 h-4 w-4" />
                  </Button>
                </Link>
              </div>
            </div>
          </section>
        </div>
      </main>
    </RetroShell>
  );
}

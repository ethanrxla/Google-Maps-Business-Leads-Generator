import './globals.css';
import type { Metadata } from 'next';
import { WalletStatus } from '@/components/wallet-status';
import { CookieConsent } from '@/components/CookieConsent';

export const metadata: Metadata = {
  title: 'Lead Packs - Instant Local Leads for Your Business',
  description: 'AI-enriched, ready-to-use lead data with phone numbers, emails, quality scores, and outreach copy. Download CSV or JSONL instantly after purchase.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="font-sans">
        {children}
        <div className="fixed bottom-4 right-4 z-50">
          <WalletStatus />
        </div>
        <CookieConsent />
      </body>
    </html>
  );
}

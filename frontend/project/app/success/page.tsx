'use client';

import { useEffect, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { getDownloadInfo, getDownloadUrl, type DownloadFormat } from '@/lib/api';
import { CheckCircle2, Download, FileText, Home, AlertCircle } from 'lucide-react';

export default function SuccessPage() {
  const searchParams = useSearchParams();
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [formats, setFormats] = useState<DownloadFormat[]>(['csv', 'jsonl']);
  const [isHarvest, setIsHarvest] = useState(false);

  useEffect(() => {
    const id = searchParams.get('session_id');
    setSessionId(id);
    if (id) {
      getDownloadInfo(id)
        .then((info) => {
          setFormats(info.formats);
          setIsHarvest(info.is_harvest);
        })
        .catch((err) => {
          console.error('download-info failed', err);
        });
    }
  }, [searchParams]);

  if (!sessionId) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background px-4">
        <Card className="w-full max-w-md">
          <CardHeader>
            <div className="mb-4 flex justify-center">
              <AlertCircle className="h-16 w-16 text-destructive" />
            </div>
            <CardTitle className="text-center">No Session Found</CardTitle>
            <CardDescription className="text-center">
              We could not find your checkout session. Please try generating a new pack.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Link href="/generate" className="block">
              <Button className="w-full" size="lg">
                Generate a Pack
              </Button>
            </Link>
          </CardContent>
        </Card>
      </div>
    );
  }

  const primaryFormat = formats[0] || 'csv';
  const secondaryFormat = formats[1] || (primaryFormat === 'csv' ? 'jsonl' : 'csv');
  const primaryUrl = getDownloadUrl(sessionId, primaryFormat);
  const secondaryUrl = getDownloadUrl(sessionId, secondaryFormat);
  const primaryLabel = isHarvest ? primaryFormat.toUpperCase() : primaryFormat.toUpperCase();
  const secondaryLabel = isHarvest ? secondaryFormat.toUpperCase() : secondaryFormat.toUpperCase();

  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-4 py-16">
      <div className="w-full max-w-2xl">
        <Card>
          <CardHeader className="text-center">
            <div className="mb-4 flex justify-center">
              <div className="rounded-full bg-green-100 p-3 dark:bg-green-900/20">
                <CheckCircle2 className="h-16 w-16 text-green-600 dark:text-green-400" />
              </div>
            </div>
            <CardTitle className="text-3xl">Payment Successful!</CardTitle>
            <CardDescription className="text-base">
              Your lead pack has been generated and is ready to download
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="rounded-lg border bg-muted/50 p-6">
              <h3 className="mb-4 text-lg font-semibold">Download Your Pack</h3>
              <p className="mb-4 text-sm text-muted-foreground">
                Choose your preferred format below. Both files contain the same data.
              </p>
              <div className="grid gap-4 sm:grid-cols-2">
                <a href={primaryUrl} download>
                  <Button className="w-full" size="lg" variant="default">
                    <Download className="mr-2 h-4 w-4" />
                    Download {primaryLabel}
                  </Button>
                </a>
                <a href={secondaryUrl} download>
                  <Button className="w-full" size="lg" variant="outline">
                    <FileText className="mr-2 h-4 w-4" />
                    Download {secondaryLabel}
                  </Button>
                </a>
              </div>
            </div>

            <div className="rounded-lg border-l-4 border-blue-500 bg-blue-50 p-4 dark:bg-blue-950/20">
              <h4 className="mb-1 text-sm font-semibold text-blue-900 dark:text-blue-100">
                File Not Ready?
              </h4>
              <p className="text-sm text-blue-800 dark:text-blue-200">
                If your download does not start or shows an error, your pack may still be processing.
                Please wait a few seconds and try again.
              </p>
            </div>

            <div className="space-y-3">
              <h3 className="text-sm font-semibold">Whats Included:</h3>
              <ul className="space-y-2 text-sm text-muted-foreground">
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="mt-0.5 h-4 w-4 flex-shrink-0 text-green-600" />
                  <span>Business names and addresses</span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="mt-0.5 h-4 w-4 flex-shrink-0 text-green-600" />
                  <span>Phone numbers and email addresses (when available)</span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="mt-0.5 h-4 w-4 flex-shrink-0 text-green-600" />
                  <span>AI-generated quality scores</span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="mt-0.5 h-4 w-4 flex-shrink-0 text-green-600" />
                  <span>Custom outreach copy for each lead</span>
                </li>
              </ul>
            </div>

            <div className="flex flex-col gap-3 pt-4 sm:flex-row">
              <Link href="/generate" className="flex-1">
                <Button className="w-full" variant="outline" size="lg">
                  Generate Another Pack
                </Button>
              </Link>
              <Link href="/" className="flex-1">
                <Button className="w-full" variant="ghost" size="lg">
                  <Home className="mr-2 h-4 w-4" />
                  Back to Home
                </Button>
              </Link>
            </div>
          </CardContent>
        </Card>

        <div className="mt-8 text-center text-sm text-muted-foreground">
          <p>
            Need help? Contact us at{' '}
            <a href="mailto:support@example.com" className="underline hover:text-foreground">
              support@example.com
            </a>
          </p>
        </div>
      </div>
    </div>
  );
}

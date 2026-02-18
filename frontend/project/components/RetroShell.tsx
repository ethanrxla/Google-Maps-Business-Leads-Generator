'use client';

import Image from 'next/image';
import { ReactNode } from 'react';

interface RetroShellProps {
  children: ReactNode;
}

export function RetroShell({ children }: RetroShellProps) {
  return (
    <div className="relative min-h-screen bg-[url('/retro/background.jpg')] bg-repeat">
      <div className="absolute inset-0 bg-gradient-to-b from-black/30 via-white/60 to-black/20 pointer-events-none" />
      <div className="relative">
        {children}
      </div>
    </div>
  );
}

export function RetroHeader() {
  return (
    <header className="border-b-4 border-yellow-300 bg-gradient-to-r from-cyan-500 via-purple-500 to-pink-500 shadow-[0_10px_30px_rgba(0,0,0,0.35)]">
      <div className="mx-auto flex max-w-7xl flex-col items-center justify-between gap-3 px-4 py-4 sm:flex-row sm:items-center">
        <div className="flex items-center gap-3">
          <div className="relative h-24 w-64 drop-shadow-[0_0_12px_rgba(0,0,0,0.5)] md:h-28 md:w-72">
            <Image
              src="/retro/lead-store-logo.png"
              alt="Lead Store"
              fill
              sizes="240px"
              className="object-contain"
            />
          </div>
          <div className="rounded-md border-2 border-yellow-200 bg-black/40 px-3 py-2 text-xs uppercase tracking-widest text-yellow-100 shadow-inner">
            Lead Store
          </div>
        </div>
        <div className="relative h-32 w-32 sm:h-40 sm:w-40">
          <Image
            src="/retro/gif.gif"
            alt="retro badge"
            fill
            className="object-contain drop-shadow-[0_0_14px_rgba(255,255,255,0.65)]"
          />
        </div>
        <div className="flex flex-col items-center gap-2 text-xs text-yellow-50 sm:flex-row">
          <span className="rounded-md border border-white/40 bg-black/30 px-3 py-1 shadow-lg shadow-yellow-400/30">
            Instant Downloads
          </span>
          <span className="rounded-md border border-white/40 bg-black/30 px-3 py-1 shadow-lg shadow-yellow-400/30">
            Secure Checkout
          </span>
          <span className="rounded-md border border-white/40 bg-black/30 px-3 py-1 shadow-lg shadow-yellow-400/30">
            AI-Enriched Leads
          </span>
        </div>
      </div>
      <div className="bg-black/70 text-center text-xs text-yellow-200 shadow-inner overflow-hidden">
        <style>
          {`
            @keyframes marquee {
              0% { transform: translateX(100%); }
              100% { transform: translateX(-100%); }
            }
            .marquee-text {
              animation: marquee 15s linear infinite;
              white-space: nowrap;
              display: inline-block;
            }
          `}
        </style>
        <div className="py-2">
          <span className="marquee-text">
            🚀 New! Enriched Packs with Apollo & Hunter • 💾 Single-Domain OSINT Scans • 🪙 Crypto checkout coming soon • 🔒 Wallet login available
          </span>
        </div>
      </div>
    </header>
  );
}

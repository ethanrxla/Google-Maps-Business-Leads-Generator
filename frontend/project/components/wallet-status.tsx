'use client';

import { useWalletSession } from '@/hooks/useWalletSession';
import { hasWalletProvider } from '@/lib/wallet';
import { useEffect, useState } from 'react';

export function WalletStatus() {
  const { address, connect } = useWalletSession();
  const [isClient, setIsClient] = useState(false);

  useEffect(() => {
    setIsClient(true);
  }, []);

  if (address) {
    return <div className="text-xs text-muted-foreground">Connected: {address.slice(0, 6)}…{address.slice(-4)}</div>;
  }

  const available = isClient && hasWalletProvider();

  return (
    <button
      onClick={connect}
      disabled={!available}
      className="rounded-md border px-3 py-2 text-xs font-semibold hover:bg-muted disabled:cursor-not-allowed disabled:opacity-50"
    >
      {available ? 'Sign In With Wallet' : 'Wallet not available'}
    </button>
  );
}

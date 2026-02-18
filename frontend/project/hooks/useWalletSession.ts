'use client';

import { useCallback, useEffect, useState } from 'react';
import { connectWallet, getNonce, signNonce, verifySignatureWithBackend, SupportedChain } from '@/lib/wallet';
import { track } from '@/lib/analytics';

export function useWalletSession() {
  const [address, setAddress] = useState<string | null>(null);
  const [chain, setChain] = useState<SupportedChain>('eth');

  useEffect(() => {
    // future: validate existing session via backend
  }, []);

  const connect = useCallback(async () => {
    try {
      const walletAddress = await connectWallet(chain);
      const nonce = await getNonce(walletAddress, chain);
      const signature = await signNonce(walletAddress, nonce, chain);
      await verifySignatureWithBackend(walletAddress, signature, nonce, chain);
      setAddress(walletAddress);
      track('wallet_login', { chain, wallet: walletAddress });
    } catch (err) {
      console.error('wallet connect failed', err);
      track('wallet_login_failed', { chain });
    }
  }, [chain]);

  return { address, chain, setChain, connect };
}

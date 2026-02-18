import { BACKEND_URL } from './config';

export type SupportedChain = 'eth' | 'sol';

export async function getNonce(walletAddress: string, chain: SupportedChain): Promise<string> {
  const res = await fetch(`${BACKEND_URL}/auth/wallet/nonce`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ wallet_address: walletAddress, chain }),
  });
  const data = await res.json();
  return data.nonce;
}

async function signMessage(provider: any, message: string, chain: SupportedChain): Promise<string> {
  if (chain === 'eth' && provider?.request) {
    return await provider.request({
      method: 'personal_sign',
      params: [message, provider.selectedAddress || provider.accounts?.[0]],
    });
  }
  if (chain === 'sol' && provider?.signMessage) {
    const encoded = new TextEncoder().encode(message);
    const signature = await provider.signMessage(encoded, 'utf8');
    return Array.from(signature.signature || signature).join(',');
  }
  throw new Error('No wallet provider found');
}

async function getProvider(chain: SupportedChain): Promise<any> {
  if (chain === 'eth') {
    if (typeof (window as any).ethereum !== 'undefined') return (window as any).ethereum;
    if (typeof (window as any).coinbaseWalletExtension !== 'undefined') return (window as any).coinbaseWalletExtension;
  }
  if (chain === 'sol') {
    if (typeof (window as any).solana !== 'undefined') return (window as any).solana;
    if (typeof (window as any).phantom?.solana !== 'undefined') return (window as any).phantom.solana;
  }
  throw new Error('Wallet provider not available');
}

export async function connectWallet(chain: SupportedChain): Promise<string> {
  const provider = await getProvider(chain);
  if (chain === 'eth' && provider.request) {
    const accounts = await provider.request({ method: 'eth_requestAccounts' });
    return accounts[0];
  }
  if (chain === 'sol' && provider.connect) {
    const res = await provider.connect();
    return res.publicKey?.toString() || provider.publicKey?.toString();
  }
  throw new Error('Failed to connect wallet');
}

export function hasWalletProvider(): boolean {
  if (typeof window === 'undefined') return false;
  const w = window as any;
  return Boolean(w.ethereum || w.coinbaseWalletExtension || w.solana || w.phantom?.solana);
}

export async function signNonce(walletAddress: string, nonce: string, chain: SupportedChain): Promise<string> {
  const provider = await getProvider(chain);
  const message = `Login to LeadOS: ${Date.now()}:${nonce}`;
  return signMessage(provider, message, chain);
}

export async function verifySignatureWithBackend(walletAddress: string, signature: string, nonce: string, chain: SupportedChain) {
  const res = await fetch(`${BACKEND_URL}/auth/wallet/verify`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ wallet_address: walletAddress, chain, signature, nonce }),
    credentials: 'include',
  });
  if (!res.ok) throw new Error('verification failed');
  return res.json();
}

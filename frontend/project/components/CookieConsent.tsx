'use client';

import { useEffect, useState } from 'react';

const PREFERENCE_KEY = 'cookie_preference';

export function CookieConsent() {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    try {
      const cookie = document.cookie
        .split(';')
        .map((c) => c.trim())
        .find((c) => c.startsWith(`${PREFERENCE_KEY}=`));
      const stored = window.localStorage.getItem(PREFERENCE_KEY);
      if (!cookie && !stored) setVisible(true);
    } catch (_) {
      setVisible(true);
    }
  }, []);

  const setPreference = (analytics: boolean) => {
    const pref = { analytics };
    try {
      window.localStorage.setItem(PREFERENCE_KEY, JSON.stringify(pref));
      const expires = new Date();
      expires.setFullYear(expires.getFullYear() + 1);
      document.cookie = `${PREFERENCE_KEY}=${encodeURIComponent(
        JSON.stringify(pref)
      )}; path=/; SameSite=Lax; expires=${expires.toUTCString()}`;
    } catch (_) {
      // ignore storage errors
    }
    setVisible(false);
  };

  if (!visible) return null;

  return (
    <div className="fixed bottom-4 left-0 right-0 z-50 flex justify-center">
      <div className="mx-4 max-w-3xl rounded-md bg-primary text-primary-foreground shadow-lg">
        <div className="flex flex-col gap-3 p-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="text-sm font-semibold">We use first-party analytics to improve the experience.</p>
            <p className="text-xs opacity-90">You can opt out of analytics any time.</p>
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => setPreference(false)}
              className="rounded-md bg-white/10 px-3 py-2 text-sm"
            >
              Decline
            </button>
            <button
              onClick={() => setPreference(true)}
              className="rounded-md bg-white px-3 py-2 text-sm font-semibold text-primary"
            >
              Accept
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

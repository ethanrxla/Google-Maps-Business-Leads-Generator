import { BACKEND_URL } from './config';

const PREF_KEY = 'cookie_preference';
const SESSION_KEY = 'analytics_session_id';

export function getAnalyticsPreference(): { analytics?: boolean } {
  if (typeof window === 'undefined') return {};
  try {
    // Prefer cookie
    const cookie = document.cookie
      .split(';')
      .map((c) => c.trim())
      .find((c) => c.startsWith(`${PREF_KEY}=`));
    if (cookie) {
      const value = decodeURIComponent(cookie.split('=')[1]);
      return JSON.parse(value);
    }
    const stored = window.localStorage.getItem(PREF_KEY);
    return stored ? JSON.parse(stored) : {};
  } catch (_) {
    return {};
  }
}

function getSessionId(): string {
  if (typeof window === 'undefined') return '';
  let sid = window.localStorage.getItem(SESSION_KEY);
  if (!sid) {
    sid = crypto.randomUUID();
    window.localStorage.setItem(SESSION_KEY, sid);
  }
  return sid;
}

export async function track(eventName: string, props: Record<string, any> = {}): Promise<void> {
  if (typeof window === 'undefined') return;
  const pref = getAnalyticsPreference();
  if (pref.analytics !== true) return;

  const session_id = getSessionId();
  const payload = {
    event_name: eventName,
    session_id,
    properties: {
      ...props,
      userAgent: navigator.userAgent,
      referrer: document.referrer,
    },
  };

  try {
    await fetch(`${BACKEND_URL}/analytics/event`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
      credentials: 'include',
    });
  } catch (err) {
    // swallow errors for now
    console.error('analytics track failed', err);
  }
}

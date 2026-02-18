import { AlertCircle, X } from 'lucide-react';
import { cn } from '@/lib/utils';

interface ErrorBannerProps {
  message: string;
  onDismiss?: () => void;
  className?: string;
}

export function ErrorBanner({ message, onDismiss, className }: ErrorBannerProps) {
  return (
    <div
      className={cn(
        'flex items-center gap-3 rounded-lg border border-destructive/50 bg-destructive/10 p-4 text-destructive',
        className
      )}
    >
      <AlertCircle className="h-5 w-5 flex-shrink-0" />
      <p className="flex-1 text-sm">{message}</p>
      {onDismiss && (
        <button
          onClick={onDismiss}
          className="flex-shrink-0 rounded-sm opacity-70 transition-opacity hover:opacity-100"
        >
          <X className="h-4 w-4" />
          <span className="sr-only">Dismiss</span>
        </button>
      )}
    </div>
  );
}

import { cn } from '@/lib/utils';

interface PreviewCardProps {
  children: React.ReactNode;
  className?: string;
}

export function PreviewCard({ children, className }: PreviewCardProps) {
  return (
    <div
      className={cn(
        'rounded-lg border bg-muted/50 p-6 shadow-sm',
        className
      )}
    >
      {children}
    </div>
  );
}

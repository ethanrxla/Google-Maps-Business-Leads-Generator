import { cn } from '@/lib/utils';

interface FormCardProps {
  children: React.ReactNode;
  className?: string;
}

export function FormCard({ children, className }: FormCardProps) {
  return (
    <div className={cn('rounded-lg border bg-card p-6 shadow-sm', className)}>
      {children}
    </div>
  );
}

/**
 * Badge Component
 * Status badges with color variants
 */

import { clsx } from 'clsx';

const Badge = ({
  children,
  variant = 'default',
  size = 'md',
  className = '',
}) => {
  const variants = {
    default: 'bg-gray-700 text-gray-200',
    primary: 'bg-primary/20 text-primary border border-primary/30',
    success: 'bg-success/20 text-success border border-success/30',
    warning: 'bg-warning/20 text-warning border border-warning/30',
    danger: 'bg-danger/20 text-danger border border-danger/30',
    info: 'bg-blue-500/20 text-blue-400 border border-blue-500/30',
    low: 'bg-gray-700 text-gray-300',
    medium: 'bg-warning/20 text-warning border border-warning/30',
    high: 'bg-orange-500/20 text-orange-400 border border-orange-500/30',
    critical: 'bg-danger/20 text-danger border border-danger/30',
  };

  const sizes = {
    sm: 'px-2 py-0.5 text-xs',
    md: 'px-2.5 py-1 text-sm',
    lg: 'px-3 py-1.5 text-base',
  };

  return (
    <span
      className={clsx(
        'inline-flex items-center font-medium rounded-full',
        variants[variant],
        sizes[size],
        className
      )}
    >
      {children}
    </span>
  );
};

export default Badge;

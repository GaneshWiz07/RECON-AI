/**
 * Card Component
 * Reusable card container with optional title and actions
 */

import { clsx } from 'clsx';

const Card = ({
  children,
  title,
  subtitle,
  action,
  className = '',
  padding = true,
  ...props
}) => {
  return (
    <div
      className={clsx(
        'glass-card glass-hover rounded-xl fade-in',
        className
      )}
      {...props}
    >
      {(title || action) && (
        <div className="px-4 sm:px-6 py-4 border-b border-white/10 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
          <div>
            {title && (
              <h3 className="text-lg font-semibold text-white">{title}</h3>
            )}
            {subtitle && (
              <p className="text-sm text-gray-400 mt-1">{subtitle}</p>
            )}
          </div>
          {action && <div>{action}</div>}
        </div>
      )}

      <div className={clsx(padding && 'p-4 sm:p-6')}>
        {children}
      </div>
    </div>
  );
};

export default Card;

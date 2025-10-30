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
        'bg-gray-800 border border-gray-700 rounded-lg shadow-lg',
        className
      )}
      {...props}
    >
      {(title || action) && (
        <div className="px-6 py-4 border-b border-gray-700 flex items-center justify-between">
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

      <div className={clsx(padding && 'p-6')}>
        {children}
      </div>
    </div>
  );
};

export default Card;

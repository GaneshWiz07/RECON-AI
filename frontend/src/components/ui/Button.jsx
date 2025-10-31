/**
 * Button Component
 * Reusable button with multiple variants and states
 */

import { clsx } from 'clsx';

const Button = ({
  children,
  variant = 'primary',
  size = 'md',
  disabled = false,
  loading = false,
  className = '',
  type = 'button',
  onClick,
  ...props
}) => {
  const baseStyles = 'font-medium rounded-lg transition-all duration-300 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-gray-900 disabled:opacity-50 disabled:cursor-not-allowed transform hover:scale-105 active:scale-95';

  const variants = {
    primary: 'bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 text-white shadow-lg hover:shadow-blue-500/50 focus:ring-blue-500',
    secondary: 'glass-card glass-hover text-white shadow-md focus:ring-gray-500',
    outline: 'border-2 border-blue-500/50 text-blue-400 hover:bg-blue-500/20 backdrop-blur-sm focus:ring-blue-500',
    ghost: 'text-gray-300 hover:bg-gray-800/50 hover:text-white backdrop-blur-sm focus:ring-gray-600',
    danger: 'bg-gradient-to-r from-red-500 to-pink-600 hover:from-red-600 hover:to-pink-700 text-white shadow-lg hover:shadow-red-500/50 focus:ring-red-500',
  };

  const sizes = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-4 py-2 text-base',
    lg: 'px-6 py-3 text-lg',
  };

  return (
    <button
      type={type}
      disabled={disabled || loading}
      onClick={onClick}
      className={clsx(
        baseStyles,
        variants[variant],
        sizes[size],
        className
      )}
      {...props}
    >
      {loading ? (
        <span className="flex items-center justify-center gap-2">
          <div className="relative w-5 h-5">
            <div className="absolute inset-0 rounded-full border-2 border-white/20"></div>
            <div className="absolute inset-0 rounded-full border-2 border-transparent border-t-white animate-spin"></div>
          </div>
          <span>Loading...</span>
        </span>
      ) : children}
    </button>
  );
};

export default Button;

/**
 * Loading Spinner Component
 * Smooth animated loading spinner with glassmorphism effect
 */

const LoadingSpinner = ({ size = 'md', className = '' }) => {
  const sizes = {
    sm: 'w-6 h-6',
    md: 'w-12 h-12',
    lg: 'w-16 h-16',
    xl: 'w-24 h-24'
  };

  return (
    <div className={`flex items-center justify-center ${className}`}>
      <div className="relative">
        {/* Outer ring */}
        <div className={`${sizes[size]} rounded-full border-4 border-blue-500/20`}></div>
        
        {/* Spinning gradient ring */}
        <div 
          className={`${sizes[size]} absolute top-0 left-0 rounded-full border-4 border-transparent border-t-blue-500 border-r-purple-500 animate-spin`}
          style={{ animationDuration: '1s' }}
        ></div>
        
        {/* Inner glow */}
        <div 
          className={`absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 ${
            size === 'sm' ? 'w-3 h-3' : 
            size === 'md' ? 'w-6 h-6' : 
            size === 'lg' ? 'w-8 h-8' : 
            'w-12 h-12'
          } rounded-full bg-gradient-to-br from-blue-500 to-purple-500 blur-md opacity-50 animate-pulse`}
        ></div>
      </div>
    </div>
  );
};

// Full screen loading overlay with glassmorphism
export const LoadingOverlay = ({ message = 'Loading...' }) => {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-gray-900/80 backdrop-blur-md">
      <div className="glass-card p-8 rounded-2xl flex flex-col items-center gap-4">
        <LoadingSpinner size="lg" />
        <p className="text-white font-medium">{message}</p>
      </div>
    </div>
  );
};

export default LoadingSpinner;


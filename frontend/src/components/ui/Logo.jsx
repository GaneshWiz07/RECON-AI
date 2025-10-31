/**
 * ReconAI Logo Component
 * SVG logo with customizable size and color
 */

const Logo = ({ size = 'md', className = '' }) => {
  const sizes = {
    sm: 'w-8 h-8',
    md: 'w-10 h-10',
    lg: 'w-12 h-12',
    xl: 'w-16 h-16'
  };

  return (
    <div className={`flex items-center gap-3 ${className}`}>
      {/* Logo Icon */}
      <div className={`${sizes[size]} relative`}>
        <svg viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
          {/* Outer Shield */}
          <path 
            d="M50 5 L85 20 L85 45 C85 65 70 82 50 95 C30 82 15 65 15 45 L15 20 Z" 
            fill="url(#shield-gradient)"
            stroke="url(#border-gradient)"
            strokeWidth="2"
          />
          
          {/* Radar Scanner Effect */}
          <circle cx="50" cy="50" r="20" fill="none" stroke="url(#radar-gradient)" strokeWidth="2" opacity="0.6"/>
          <circle cx="50" cy="50" r="15" fill="none" stroke="url(#radar-gradient)" strokeWidth="1.5" opacity="0.4"/>
          <circle cx="50" cy="50" r="10" fill="none" stroke="url(#radar-gradient)" strokeWidth="1" opacity="0.3"/>
          
          {/* Center Dot */}
          <circle cx="50" cy="50" r="3" fill="#60A5FA"/>
          
          {/* Scanning Line (animated) */}
          <line x1="50" y1="50" x2="50" y2="30" stroke="#60A5FA" strokeWidth="2" strokeLinecap="round" opacity="0.8">
            <animateTransform
              attributeName="transform"
              type="rotate"
              from="0 50 50"
              to="360 50 50"
              dur="3s"
              repeatCount="indefinite"
            />
          </line>
          
          {/* Gradients */}
          <defs>
            <linearGradient id="shield-gradient" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" style={{ stopColor: '#3B82F6', stopOpacity: 0.3 }} />
              <stop offset="100%" style={{ stopColor: '#8B5CF6', stopOpacity: 0.2 }} />
            </linearGradient>
            
            <linearGradient id="border-gradient" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" style={{ stopColor: '#60A5FA', stopOpacity: 0.8 }} />
              <stop offset="100%" style={{ stopColor: '#A78BFA', stopOpacity: 0.8 }} />
            </linearGradient>
            
            <linearGradient id="radar-gradient" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" style={{ stopColor: '#60A5FA', stopOpacity: 1 }} />
              <stop offset="100%" style={{ stopColor: '#A78BFA', stopOpacity: 1 }} />
            </linearGradient>
          </defs>
        </svg>
      </div>
      
      {/* Logo Text */}
      {size !== 'sm' && (
        <div className="flex flex-col">
          <span className="text-white font-bold text-xl tracking-tight" style={{ fontFamily: "'Space Grotesk', sans-serif" }}>
            Recon<span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-400">AI</span>
          </span>
          <span className="text-[10px] text-gray-400 tracking-wider uppercase">Security Intelligence</span>
        </div>
      )}
    </div>
  );
};

export default Logo;


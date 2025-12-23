import React from 'react';

export const TechBackground: React.FC = () => {
  return (
    <>
      {/* Digital Circuit / Grid Overlay */}
      <div className="absolute inset-0 z-0 opacity-20 pointer-events-none" 
           style={{
             backgroundImage: 'radial-gradient(circle, currentColor 1px, transparent 1px)',
             backgroundSize: '4px 4px'
           }}
      />

      {/* Continuous Flowing Energy Background */}
      <div className="absolute inset-0 pointer-events-none z-0">
        <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/40 to-transparent -translate-x-full animate-shimmer skew-x-12" />
      </div>

      {/* Decorative corner accents for tech feel */}
      <div className="absolute top-0 left-0 w-2 h-2 border-t border-l border-current opacity-50 group-hover:opacity-100 transition-opacity" />
      <div className="absolute bottom-0 right-0 w-2 h-2 border-b border-r border-current opacity-50 group-hover:opacity-100 transition-opacity" />
    </>
  );
};
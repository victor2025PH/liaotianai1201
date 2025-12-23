import React from 'react';
import { ArrowRight } from 'lucide-react';
import { TechBackground } from './TechBackground';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline';
  icon?: boolean;
}

export const Button: React.FC<ButtonProps> = ({ 
  children, 
  variant = 'primary', 
  icon = false,
  className = '',
  ...props 
}) => {
  const baseStyles = "relative group px-6 py-3 font-mono text-sm font-bold tracking-wider uppercase transition-all duration-300 ease-out clip-path-slant overflow-hidden";
  
  const variants = {
    primary: "bg-cyan-500 text-black hover:bg-cyan-400 hover:shadow-[0_0_20px_rgba(6,182,212,0.6)] hover:scale-105 active:scale-95",
    secondary: "bg-white/5 border border-white/10 text-white hover:bg-white/10 hover:border-cyan-500/50 hover:text-cyan-400 hover:scale-105 active:scale-95",
    outline: "border border-white/20 text-zinc-400 hover:border-white/80 hover:text-white"
  };

  return (
    <button 
      className={`${baseStyles} ${variants[variant]} ${className}`}
      {...props}
    >
      <TechBackground />

      <span className="relative z-10 flex items-center gap-2">
        {children}
        {icon && (
          <ArrowRight className="w-4 h-4 transition-transform group-hover:translate-x-1" />
        )}
      </span>
    </button>
  );
};
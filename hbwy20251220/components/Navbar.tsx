import React from 'react';
import { Gift } from 'lucide-react';

export const Navbar = () => {
  return (
    <nav className="fixed top-0 left-0 right-0 z-40 border-b border-white/5 bg-game-dark/80 backdrop-blur-md">
      <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="bg-gradient-primary p-1.5 rounded-lg">
            <Gift className="text-white w-5 h-5" />
          </div>
          <span className="font-display font-bold text-xl tracking-wide">
            Red<span className="text-game-primary">Envelope</span>.fi
          </span>
        </div>
        <div className="hidden md:flex items-center gap-8 text-sm font-medium text-gray-400">
          <a href="#mechanic" className="hover:text-white transition-colors">核心机制</a>
          <a href="#modes" className="hover:text-white transition-colors">玩法模式</a>
          <a href="#tech" className="hover:text-white transition-colors">技术架构</a>
          <button className="px-6 py-2 bg-white/5 hover:bg-white/10 text-white font-bold border border-white/10 rounded-full transition-all duration-300">
            Book Demo
          </button>
        </div>
      </div>
    </nav>
  );
};
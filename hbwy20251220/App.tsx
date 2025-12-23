import React, { useState, useEffect } from 'react';
import { Hero } from './components/Hero';
import { Mechanic } from './components/Mechanic';
import { GameModes } from './components/GameModes';
import { Technical } from './components/Technical';
import { Revenue } from './components/Revenue';
import { Footer } from './components/Footer';
import { Navbar } from './components/Navbar';
import { AIChatProvider } from './contexts/AIChatContext';
import { AISprite } from './components/AISprite';
import { AIChatTerminal } from './components/AIChatTerminal';

// Global Scroll Progress Bar
const ScrollProgress = () => {
  const [scrollProgress, setScrollProgress] = useState(0);

  useEffect(() => {
    const handleScroll = () => {
      const totalScroll = document.documentElement.scrollTop;
      const windowHeight = document.documentElement.scrollHeight - document.documentElement.clientHeight;
      const scroll = `${totalScroll / windowHeight}`;
      setScrollProgress(Number(scroll));
    };

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  return (
    <div className="fixed top-0 left-0 w-full h-1 z-50 bg-gray-900">
      <div 
        className="h-full bg-gradient-primary shadow-[0_0_10px_#FF6B00]"
        style={{ width: `${scrollProgress * 100}%`, transition: 'width 0.1s' }}
      />
    </div>
  );
};

export default function App() {
  return (
    <AIChatProvider>
      <div className="min-h-screen bg-game-dark text-white selection:bg-game-primary selection:text-white overflow-hidden">
        <ScrollProgress />
        <Navbar />
        
        <main className="relative z-10">
          <Hero />
          <Mechanic />
          <GameModes />
          <Technical />
          <Revenue />
        </main>

        <Footer />
        
        {/* AI Robot and Chat */}
        <AISprite />
        <AIChatTerminal />
        
        {/* Background Ambience */}
        <div className="fixed inset-0 z-0 pointer-events-none">
          <div className="absolute top-[-10%] left-[20%] w-[30%] h-[30%] bg-game-primary/10 rounded-full blur-[120px]" />
          <div className="absolute top-[40%] right-[-10%] w-[40%] h-[40%] bg-game-secondary/10 rounded-full blur-[150px]" />
          <div className="absolute bottom-[-10%] left-[-10%] w-[40%] h-[40%] bg-game-primary/5 rounded-full blur-[120px]" />
        </div>
      </div>
    </AIChatProvider>
  );
}
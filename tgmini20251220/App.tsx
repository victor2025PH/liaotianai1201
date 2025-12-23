import React from 'react';
import Navbar from './components/Navbar';
import Hero from './components/Hero';
import FutureParticles from './components/FutureParticles';
import PainPoints from './components/PainPoints';
import ServiceScope from './components/ServiceScope';
import UseCases from './components/UseCases';
import TechStack from './components/TechStack';
import Pricing from './components/Pricing';
import Footer from './components/Footer';
import { AIChatProvider } from './contexts/AIChatContext';
import { AISprite } from './components/AISprite';
import { AIChatTerminal } from './components/AIChatTerminal';

const App: React.FC = () => {
  return (
    <AIChatProvider>
      <div className="min-h-screen bg-dark-bg text-white selection:bg-neon-purple selection:text-white overflow-x-hidden">
        <div className="fixed inset-0 z-0 pointer-events-none">
          <div className="absolute inset-0 bg-cyber-grid opacity-[0.07] cyber-grid-bg"></div>
          <div className="absolute top-[-20%] right-[-10%] w-[500px] h-[500px] bg-neon-purple/20 rounded-full blur-[128px]"></div>
          <div className="absolute bottom-[-20%] left-[-10%] w-[500px] h-[500px] bg-neon-blue/20 rounded-full blur-[128px]"></div>
        </div>

        <div className="relative z-10">
          <Navbar />
          <main>
            <Hero />
            <FutureParticles />
            <PainPoints />
            <ServiceScope />
            <UseCases />
            <TechStack />
            <Pricing />
          </main>
          <Footer />
        </div>
        
        {/* AI Robot and Chat */}
        <AISprite />
        <AIChatTerminal />
      </div>
    </AIChatProvider>
  );
};

export default App;
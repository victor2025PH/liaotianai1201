import React, { useState, useEffect } from 'react';
import { Menu, X, Zap } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const Navbar: React.FC = () => {
  const [isScrolled, setIsScrolled] = useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 20);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const navLinks = [
    { name: '痛点对比', href: '#pain-points' },
    { name: '服务内容', href: '#services' },
    { name: '落地场景', href: '#use-cases' },
    { name: '技术栈', href: '#tech' },
    { name: '价格套餐', href: '#pricing' },
  ];

  return (
    <nav
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 border-b ${
        isScrolled
          ? 'bg-dark-bg/80 backdrop-blur-md border-dark-border py-4'
          : 'bg-transparent border-transparent py-6'
      }`}
    >
      <div className="container mx-auto px-4 md:px-6 flex items-center justify-between">
        <div className="flex items-center gap-2 font-mono font-bold text-xl tracking-tighter">
          <div className="w-8 h-8 bg-gradient-to-br from-neon-blue to-neon-purple rounded flex items-center justify-center">
            <Zap className="text-white w-5 h-5" fill="white" />
          </div>
          <span className="bg-clip-text text-transparent bg-gradient-to-r from-white to-gray-400">
            MINIAPP<span className="text-neon-blue">.STUDIO</span>
          </span>
        </div>

        {/* Desktop Nav */}
        <div className="hidden md:flex items-center gap-8">
          {navLinks.map((link) => (
            <a
              key={link.name}
              href={link.href}
              className="text-sm text-gray-400 hover:text-white transition-colors hover:shadow-[0_0_10px_rgba(255,255,255,0.3)]"
            >
              {link.name}
            </a>
          ))}
          <a
            href="#contact"
            className="px-4 py-2 bg-white text-black font-bold text-sm rounded hover:bg-neon-blue hover:text-white transition-all duration-300"
          >
            立即咨询
          </a>
        </div>

        {/* Mobile Toggle */}
        <button
          className="md:hidden text-white"
          onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
        >
          {isMobileMenuOpen ? <X /> : <Menu />}
        </button>
      </div>

      {/* Mobile Menu */}
      <AnimatePresence>
        {isMobileMenuOpen && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="md:hidden bg-dark-card border-b border-dark-border overflow-hidden"
          >
            <div className="flex flex-col p-4 gap-4">
              {navLinks.map((link) => (
                <a
                  key={link.name}
                  href={link.href}
                  className="text-gray-300 hover:text-neon-blue py-2"
                  onClick={() => setIsMobileMenuOpen(false)}
                >
                  {link.name}
                </a>
              ))}
              <a
                href="#contact"
                className="w-full text-center py-3 bg-neon-purple text-white font-bold rounded"
                onClick={() => setIsMobileMenuOpen(false)}
              >
                立即咨询
              </a>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </nav>
  );
};

export default Navbar;
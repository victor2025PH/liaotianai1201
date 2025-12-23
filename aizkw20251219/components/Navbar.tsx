import React, { useState, useEffect } from 'react';
import { Menu, X, Globe, Terminal } from 'lucide-react';
import { useLanguage } from '../contexts/LanguageContext';
import { useAIChat } from '../contexts/AIChatContext';

// Backup SVG Logo in case image fails to load
const FallbackLogo = () => (
  <svg viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg" className="w-full h-full text-cyan-500 drop-shadow-[0_0_10px_rgba(0,255,255,0.8)]">
    <path d="M20 40L30 65H70L80 40L60 55L50 25L40 55L20 40Z" stroke="currentColor" strokeWidth="5" strokeLinecap="round" strokeLinejoin="round" />
    <path d="M30 65L35 80H65L70 65" stroke="currentColor" strokeWidth="5" strokeLinecap="round" strokeLinejoin="round" />
    <circle cx="20" cy="40" r="4" fill="#fff" className="animate-pulse" />
    <circle cx="50" cy="25" r="4" fill="#fff" className="animate-pulse" />
    <circle cx="80" cy="40" r="4" fill="#fff" className="animate-pulse" />
    <circle cx="50" cy="65" r="3" fill="currentColor" />
    <path d="M50 25V55" stroke="currentColor" strokeWidth="3" className="opacity-50" />
    <path d="M40 55L50 65L60 55" stroke="currentColor" strokeWidth="3" className="opacity-50" />
  </svg>
);

export const Navbar: React.FC = () => {
  const [scrolled, setScrolled] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [langMenuOpen, setLangMenuOpen] = useState(false);
  const [logoError, setLogoError] = useState(false);
  const { language, setLanguage, t } = useLanguage();
  const { openChat } = useAIChat();

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 50);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const navLinks = [
    { name: t('nav.capabilities'), href: '#capabilities' },
    { name: t('nav.pricing'), href: '#pricing' },
    { name: t('nav.matrix'), href: '#matrix' },
    { name: t('nav.agents'), href: '#trusted-by' }, // Updated to point to Case Studies section
    { name: t('nav.contact'), href: '#contact' },
  ];

  const languages = [
    { code: 'en', label: 'EN' },
    { code: 'cn', label: '简' },
    { code: 'tw', label: '繁' },
    { code: 'jp', label: 'JP' },
  ];

  const handleNavClick = (e: React.MouseEvent<HTMLAnchorElement>, href: string) => {
    e.preventDefault();
    setMobileMenuOpen(false);
    const targetId = href.replace('#', '');
    const element = document.getElementById(targetId);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth' });
    }
  };

  return (
    <nav 
      className={`fixed top-0 w-full z-50 transition-all duration-300 border-b ${
        scrolled 
          ? 'glass-panel border-cyan-500/10 py-3' 
          : 'bg-transparent border-transparent py-6'
      }`}
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center">
          {/* Logo & Brand */}
          <div className="flex items-center gap-6 group cursor-pointer" onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}>
            <div className="relative w-16 h-16 flex items-center justify-center">
               {/* Animated Glow Background */}
               <div className="absolute inset-0 bg-cyan-500/30 blur-2xl rounded-full animate-pulse-slow"></div>
               <div className="absolute inset-0 bg-gradient-to-tr from-cyan-400/20 to-transparent rounded-full opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
               
               {/* Logo Image with Fallback */}
               {!logoError ? (
                 <img 
                   src="/logo.png" 
                   alt="Smart Control King Logo" 
                   onError={() => setLogoError(true)}
                   className="w-full h-full object-contain relative z-10 drop-shadow-[0_0_10px_rgba(0,255,255,0.8)] group-hover:scale-110 transition-transform duration-300"
                 />
               ) : (
                 <div className="w-full h-full relative z-10 group-hover:scale-110 transition-transform duration-300">
                    <FallbackLogo />
                 </div>
               )}
               
               {/* Tech Ring Decoration */}
               <div className="absolute inset-[-4px] border border-cyan-500/30 rounded-full scale-0 group-hover:scale-100 transition-transform duration-500 opacity-0 group-hover:opacity-100"></div>
            </div>
            
            {/* Dynamic Brand Name */}
            {(language === 'cn' || language === 'tw') ? (
               <div className="flex flex-col">
                  <span className="font-sans text-2xl font-bold tracking-wider text-white group-hover:text-cyan-400 transition-colors drop-shadow-lg">
                    AI <span className="text-cyan-500 font-black drop-shadow-[0_0_8px_rgba(0,255,255,0.8)]">智控王</span>
                  </span>
                  <span className="text-[10px] font-mono text-cyan-500/70 tracking-[0.3em] uppercase">System Online</span>
               </div>
            ) : (
               <div className="flex flex-col leading-none justify-center h-full">
                 <span className="font-mono text-lg font-bold tracking-[0.15em] text-cyan-500 group-hover:text-cyan-400 drop-shadow-[0_0_5px_rgba(0,255,255,0.5)]">SMART CONTROL</span>
                 <span className="font-mono text-sm font-bold tracking-[0.4em] text-zinc-400 group-hover:text-white pl-[1px] mt-1">KING</span>
               </div>
            )}
          </div>

          {/* Desktop Nav */}
          <div className="hidden md:flex items-center gap-8">
            {navLinks.map((link) => (
              <a 
                key={link.href} 
                href={link.href}
                onClick={(e) => handleNavClick(e, link.href)}
                className="font-mono text-xs uppercase tracking-widest text-zinc-400 hover:text-cyan-400 transition-colors hover:shadow-[0_2px_10px_rgba(0,255,255,0.2)]"
              >
                <span className="text-cyan-500 mr-1 opacity-50">//</span>
                {link.name}
              </a>
            ))}
            
            {/* Language Switcher */}
            <div className="relative">
              <button 
                onClick={() => setLangMenuOpen(!langMenuOpen)}
                className="flex items-center gap-2 px-3 py-2 border border-white/10 rounded bg-white/5 text-zinc-300 hover:border-cyan-500/50 hover:text-cyan-400 transition-all font-mono text-xs"
              >
                <Globe className="w-3 h-3" />
                <span>{languages.find(l => l.code === language)?.label}</span>
              </button>
              
              {langMenuOpen && (
                <div className="absolute top-full right-0 mt-2 w-24 glass-panel border border-cyan-500/20 rounded overflow-hidden flex flex-col shadow-[0_0_20px_rgba(0,0,0,0.8)] z-50">
                  {languages.map((lang) => (
                    <button
                      key={lang.code}
                      onClick={() => {
                        setLanguage(lang.code as any);
                        setLangMenuOpen(false);
                      }}
                      className={`px-4 py-2 text-xs font-mono text-left hover:bg-cyan-900/30 transition-colors ${
                        language === lang.code ? 'text-cyan-400 bg-cyan-950/50' : 'text-zinc-400'
                      }`}
                    >
                      {lang.label}
                    </button>
                  ))}
                </div>
              )}
            </div>

            <button 
                onClick={(e) => openChat('User attempted login.', 'ACCESS DENIED: Biometric signature required.\n\nInitializing GUEST_MODE...\n\nHow can I assist you with system access or deployment today?', e.currentTarget as HTMLElement)}
                className="flex items-center gap-2 px-4 py-2 border border-cyan-500/30 text-cyan-400 font-mono text-xs uppercase tracking-wider hover:bg-cyan-500/10 hover:shadow-[0_0_10px_rgba(0,255,255,0.2)] transition-all"
            >
              <Terminal className="w-3 h-3" />
              {t('nav.login')}
            </button>
          </div>

          {/* Mobile Menu Button */}
          <div className="md:hidden flex items-center gap-4">
             {/* Mobile Language Toggle */}
            <button 
                onClick={() => {
                  const langs = ['en', 'cn', 'tw', 'jp'];
                  const currentIndex = langs.indexOf(language);
                  const nextIndex = (currentIndex + 1) % langs.length;
                  setLanguage(langs[nextIndex] as any);
                }}
                className="p-2 border border-white/10 rounded bg-white/5 text-xs font-mono text-cyan-500"
              >
                {languages.find(l => l.code === language)?.label}
            </button>

            <button 
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="p-2 text-zinc-400 hover:text-cyan-400 transition-colors"
            >
              {mobileMenuOpen ? <X /> : <Menu />}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Menu */}
      {mobileMenuOpen && (
        <div className="md:hidden glass-panel border-b border-cyan-500/20">
          <div className="px-4 pt-2 pb-6 space-y-2">
            {navLinks.map((link) => (
              <a
                key={link.href}
                href={link.href}
                onClick={(e) => handleNavClick(e, link.href)}
                className="block px-3 py-3 font-mono text-sm text-zinc-300 hover:text-cyan-400 hover:bg-cyan-950/30 rounded-md border border-transparent hover:border-cyan-500/20"
              >
                 <span className="text-cyan-500 mr-2">{'>'}</span>{link.name}
              </a>
            ))}
            <button 
                onClick={(e) => {
                    setMobileMenuOpen(false);
                    openChat('User attempted login (mobile).', 'ACCESS DENIED: Biometric signature required.\n\nInitializing GUEST_MODE...\n\nHow can I assist you?', undefined);
                }}
                className="w-full text-left px-3 py-3 font-mono text-sm text-cyan-400 hover:bg-cyan-950/30 rounded-md border border-transparent hover:border-cyan-500/20 flex items-center gap-2"
            >
               <Terminal className="w-4 h-4" />
               {t('nav.login')}
            </button>
          </div>
        </div>
      )}
    </nav>
  );
};
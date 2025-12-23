import React, { useRef } from 'react';
import { motion, useScroll, useTransform, useSpring } from 'framer-motion';

type SectionVariant = 'default' | 'glass' | 'deep' | 'grid';
type SectionDivider = 'none' | 'slant-top' | 'slant-bottom' | 'both';

interface SectionProps {
  id: string;
  title?: string;
  subtitle?: string;
  children: React.ReactNode;
  className?: string;
  allowOverflow?: boolean;
  variant?: SectionVariant;
  divider?: SectionDivider;
}

export const Section: React.FC<SectionProps> = ({ 
  id, 
  title, 
  subtitle, 
  children, 
  className = '', 
  allowOverflow = false,
  variant = 'default',
  divider = 'none'
}) => {
  const containerRef = useRef<HTMLElement>(null);
  
  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ["start end", "end start"]
  });

  const smoothProgress = useSpring(scrollYProgress, { stiffness: 100, damping: 30, restDelta: 0.001 });
  const bgY = useTransform(smoothProgress, [0, 1], [-100, 100]);
  const opacity = useTransform(smoothProgress, [0, 0.1, 0.9, 1], [0, 1, 1, 0]);
  const y = useTransform(smoothProgress, [0, 0.1], [50, 0]);

  // Visual Variants Configuration
  const variants = {
    default: "bg-transparent",
    glass: "bg-zinc-900/40 backdrop-blur-sm border-y border-white/5",
    deep: "bg-black",
    grid: "bg-zinc-950"
  };

  // Divider Styles (Clip Paths)
  const getClipPath = () => {
    switch (divider) {
      case 'slant-top': return 'polygon(0 50px, 100% 0, 100% 100%, 0 100%)';
      case 'slant-bottom': return 'polygon(0 0, 100% 0, 100% calc(100% - 50px), 0 100%)';
      case 'both': return 'polygon(0 50px, 100% 0, 100% calc(100% - 50px), 0 100%)';
      default: return 'none';
    }
  };

  return (
    <motion.section 
      ref={containerRef}
      id={id} 
      className={`py-24 relative ${allowOverflow ? '' : 'overflow-hidden'} ${variants[variant]} ${className}`}
      style={{ 
        opacity,
        clipPath: getClipPath(),
        // Add negative margins to overlap sections if slanted, ensuring no background gaps
        marginTop: divider === 'slant-top' || divider === 'both' ? '-50px' : '0',
        paddingTop: divider === 'slant-top' || divider === 'both' ? 'calc(6rem + 50px)' : '6rem',
        paddingBottom: divider === 'slant-bottom' || divider === 'both' ? 'calc(6rem + 50px)' : '6rem',
        zIndex: variant === 'deep' ? 10 : 1
      }}
    >
      {/* Background Textures */}
      {variant === 'grid' && (
        <div className="absolute inset-0 pointer-events-none opacity-[0.05] z-0 bg-[linear-gradient(to_right,#808080_1px,transparent_1px),linear-gradient(to_bottom,#808080_1px,transparent_1px)] bg-[size:4rem_4rem]" />
      )}
      
      {variant === 'deep' && (
         <div className="absolute inset-0 z-0 bg-[radial-gradient(circle_at_center,rgba(0,255,255,0.03)_0%,transparent_70%)]" />
      )}

      {/* Floating Parallax Elements (Optional Dust/Noise) */}
      <motion.div 
        style={{ y: bgY }}
        className="absolute inset-0 pointer-events-none opacity-20 z-0 mix-blend-overlay"
      >
         <div className="absolute top-0 left-1/4 w-96 h-96 bg-cyan-500/10 rounded-full blur-[100px]" />
         <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-purple-500/10 rounded-full blur-[100px]" />
      </motion.div>

      <motion.div 
        style={{ y }}
        className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10"
      >
        {/* Section Header */}
        {(title || subtitle) && (
          <div className="mb-20">
            <motion.div 
              initial={{ x: -20, opacity: 0 }}
              whileInView={{ x: 0, opacity: 1 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5 }}
              className="flex items-center gap-4 mb-6"
            >
              <div className={`h-px w-12 ${variant === 'deep' ? 'bg-cyan-500' : 'bg-zinc-700'}`}></div>
              <span className={`font-mono tracking-[0.2em] uppercase text-xs ${variant === 'deep' ? 'text-cyan-500' : 'text-zinc-500'}`}>
                0x{id.toUpperCase()}
              </span>
            </motion.div>
            
            {title && (
              <motion.h2 
                initial={{ y: 20, opacity: 0 }}
                whileInView={{ y: 0, opacity: 1 }}
                viewport={{ once: true }}
                transition={{ duration: 0.5, delay: 0.1 }}
                className="text-4xl md:text-6xl font-bold text-white mb-6 tracking-tight leading-tight"
              >
                {title}
              </motion.h2>
            )}

            {subtitle && (
              <motion.p 
                initial={{ y: 20, opacity: 0 }}
                whileInView={{ y: 0, opacity: 1 }}
                viewport={{ once: true }}
                transition={{ duration: 0.5, delay: 0.2 }}
                className="text-zinc-400 max-w-2xl text-lg md:text-xl font-light leading-relaxed border-l-2 border-zinc-800 pl-6"
              >
                {subtitle}
              </motion.p>
            )}
          </div>
        )}

        {/* Content Container */}
        <div className="relative">
          {children}
        </div>
      </motion.div>
    </motion.section>
  );
};

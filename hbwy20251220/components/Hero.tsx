import React, { useMemo, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Zap, ShieldCheck, Flame, Play } from 'lucide-react';

export const Hero = () => {
  const [showEffects, setShowEffects] = useState(true);

  // Generate random particles for the background effect
  const particles = useMemo(() => {
    return Array.from({ length: 60 }).map((_, i) => {
      const type = Math.random();
      let shape = 'bit'; // default square
      if (type > 0.7) shape = 'coin';
      else if (type > 0.4) shape = 'envelope';

      return {
        id: i,
        left: Math.random() * 100,
        size: Math.random() * 10 + 4, // 4px to 14px
        duration: Math.random() * 12 + 8, // 8s to 20s
        delay: Math.random() * 5,
        shape,
        drift: Math.random() * 100 - 50, // horizontal drift
      };
    });
  }, []);

  // Staggered Text Animation Variants
  const containerVariants = {
    hidden: { opacity: 1 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.08,
        delayChildren: 0.2,
      },
    },
  };

  const characterVariants = {
    hidden: { opacity: 0, y: 20, filter: 'blur(8px)' },
    visible: { 
      opacity: 1, 
      y: 0, 
      filter: 'blur(0px)',
      transition: {
        type: "spring",
        damping: 12,
        stiffness: 200
      }
    },
  };

  return (
    <section className="relative min-h-[90vh] flex items-center justify-center pt-24 overflow-hidden">
      
      {/* Animated Digital Particles / Confetti */}
      <AnimatePresence>
        {showEffects && (
          <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.5 }}
            className="absolute inset-0 pointer-events-none z-0 overflow-hidden"
          >
            {particles.map((p) => (
              <motion.div
                key={p.id}
                className={`absolute backdrop-blur-[1px]
                  ${p.shape === 'coin' 
                    ? 'bg-yellow-400 rounded-full shadow-[0_0_15px_rgba(250,204,21,0.4)]' 
                    : p.shape === 'envelope'
                      ? 'bg-gradient-to-br from-red-500 to-red-700 rounded-[2px] shadow-[0_0_15px_rgba(220,38,38,0.4)]'
                      : 'bg-orange-500/80 rounded-sm shadow-[0_0_10px_rgba(249,115,22,0.4)]'
                  }`}
                style={{
                  left: `${p.left}%`,
                  width: p.shape === 'envelope' ? p.size * 0.8 : p.size,
                  height: p.size,
                }}
                initial={{ y: -50, x: 0, opacity: 0, rotate: 0 }}
                animate={{
                  y: ['-10vh', '110vh'],
                  x: [0, p.drift],
                  opacity: [0, 0.8, 0],
                  rotate: [0, 360 * (p.drift > 0 ? 1 : -1)],
                  scale: [0.8, 1.2, 0.8]
                }}
                transition={{
                  duration: p.duration,
                  repeat: Infinity,
                  delay: p.delay,
                  ease: "linear",
                }}
              />
            ))}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Central Ambient Glow */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] bg-orange-600/10 rounded-full blur-[100px] pointer-events-none z-0" />

      <div className="max-w-7xl mx-auto px-6 relative z-10 text-center flex flex-col items-center">
        
        {/* Badge - Mimicking the "Good" progress bar style */}
        <motion.div 
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="inline-flex items-center gap-3 px-2 py-2 pr-4 rounded-full bg-game-card border border-white/10 mb-8 backdrop-blur-md relative z-20 hover:border-orange-500/50 transition-colors cursor-default"
        >
          <div className="bg-gradient-primary px-3 py-1 rounded-full text-xs font-bold text-white shadow-lg shadow-orange-500/30">
            NEW v3.0
          </div>
          <span className="text-gray-300 text-sm font-medium tracking-wide">
            Telegram Viral Growth Engine
          </span>
        </motion.div>

        {/* Main Headline */}
        <motion.h1 
          className="font-display text-5xl md:text-7xl lg:text-8xl font-black leading-tight mb-6 max-w-5xl relative z-20 text-center"
          initial="hidden"
          animate="visible"
          variants={containerVariants}
        >
          <span className="block text-white drop-shadow-xl">
            {"TG 生态最强".split("").map((char, index) => (
              <motion.span 
                key={index} 
                variants={characterVariants}
                className="inline-block"
              >
                {char === " " ? "\u00A0" : char}
              </motion.span>
            ))}
          </span>
          
          <motion.span 
            className="block mt-2 text-transparent bg-clip-text bg-gradient-to-r from-orange-400 via-red-500 to-purple-600 bg-[length:200%_auto] text-glow pb-2"
            variants={characterVariants}
            animate={{ 
              backgroundPosition: ["0% 50%", "200% 50%"],
            }}
            transition={{ 
              backgroundPosition: { duration: 3, repeat: Infinity, ease: "linear" },
            }}
          >
             裂变核武器
          </motion.span>
        </motion.h1>

        {/* Subheadline */}
        <motion.p 
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.7, delay: 0.8 }}
          className="text-gray-400 text-lg md:text-xl max-w-2xl mb-10 leading-relaxed font-medium relative z-20"
        >
          别再做无聊的营销活动了。利用 <span className="text-white font-bold border-b border-orange-500/50">USDT/TON</span> 真金白银的刺激，
          打造一款让用户疯狂转发、自发拉人的现象级 Mini App。
        </motion.p>

        {/* Stats/Tags - Styled like game stats */}
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, delay: 1.0 }}
          className="flex flex-wrap justify-center gap-4 mb-12 relative z-20"
        >
          {[
            { icon: Flame, text: "指数级裂变", color: "text-orange-500" },
            { icon: ShieldCheck, text: "链上资金托管", color: "text-green-500" },
            { icon: Zap, text: "万人并发秒开", color: "text-yellow-500" }
          ].map((tag, idx) => (
            <div key={idx} className="flex items-center gap-2 px-5 py-2.5 bg-game-card border border-white/5 rounded-2xl shadow-xl backdrop-blur-sm hover:bg-white/5 transition-colors">
              <tag.icon size={18} className={tag.color} />
              <span className="text-sm font-bold text-gray-200">{tag.text}</span>
            </div>
          ))}
        </motion.div>

        {/* CTA Buttons - Matching "Send Packet" Style */}
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, delay: 1.2 }}
          className="flex flex-col md:flex-row gap-6 w-full max-w-md md:max-w-none justify-center relative z-20"
        >
          <button className="group relative px-8 py-5 bg-gradient-primary text-white font-display font-bold text-lg rounded-2xl shadow-[0_10px_40px_-10px_rgba(255,107,0,0.5)] hover:shadow-[0_20px_60px_-10px_rgba(255,107,0,0.6)] hover:-translate-y-1 transition-all duration-300 overflow-hidden">
            <div className="absolute inset-0 bg-white/20 translate-y-full group-hover:translate-y-0 transition-transform duration-300"></div>
            <span className="relative flex items-center justify-center gap-3">
              <Flame className="w-6 h-6 fill-white animate-bounce" />
              立即引爆我的流量
            </span>
          </button>
          
          <button className="group px-8 py-5 bg-game-card border border-white/10 text-white font-display font-bold text-lg rounded-2xl hover:bg-white/5 transition-all duration-300">
            <span className="flex items-center justify-center gap-3">
              <Play className="w-5 h-5 fill-current text-game-secondary group-hover:text-white transition-colors" />
              体验演示 Demo
            </span>
          </button>
        </motion.div>

        {/* Floating Game Elements - Kept as background accents */}
        <div className="absolute top-1/4 left-[10%] opacity-30 animate-float hidden lg:block z-0">
          <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-orange-400 to-red-600 rotate-12 blur-[2px] shadow-lg shadow-orange-500/20"></div>
        </div>
        <div className="absolute bottom-1/4 right-[10%] opacity-30 animate-float hidden lg:block z-0" style={{ animationDelay: '1.5s' }}>
           <div className="w-20 h-20 rounded-full bg-gradient-to-br from-purple-500 to-blue-600 blur-[2px] shadow-lg shadow-purple-500/20"></div>
        </div>

      </div>

      {/* Decorative Bottom Fade */}
      <div className="absolute bottom-0 left-0 right-0 h-32 bg-gradient-to-t from-game-dark to-transparent z-10 pointer-events-none" />

      {/* Effects Toggle Button */}
      <div className="absolute bottom-4 right-4 z-50">
        <button 
          onClick={() => setShowEffects(!showEffects)}
          className={`text-xs font-medium px-3 py-1.5 rounded-full border transition-all duration-300 backdrop-blur-md ${
            showEffects 
              ? 'bg-white/10 text-white border-white/20 shadow-[0_0_10px_rgba(255,107,0,0.2)]' 
              : 'bg-black/20 text-gray-500 border-white/5 hover:text-gray-300 hover:bg-white/5'
          }`}
        >
          Toggle Effects
        </button>
      </div>

    </section>
  );
};
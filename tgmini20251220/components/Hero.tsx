import React from 'react';
import { motion } from 'framer-motion';
import { ArrowRight, Sparkles, Zap, ShieldCheck } from 'lucide-react';

const Hero: React.FC = () => {
  return (
    <section className="relative pt-32 pb-20 md:pt-48 md:pb-32 overflow-hidden">
      <div className="container mx-auto px-4 text-center relative z-10">
        
        {/* Badge */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, ease: "easeOut" }}
          className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/5 border border-white/10 text-neon-blue text-xs font-mono mb-8 backdrop-blur-sm"
        >
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-neon-blue opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-neon-blue"></span>
          </span>
          Telegram Ecosystem Builder
        </motion.div>

        {/* Main Title */}
        <motion.h1
          initial={{ opacity: 0, y: 50 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, ease: "easeOut", delay: 0.2 }}
          className="text-4xl md:text-6xl lg:text-7xl font-black tracking-tighter mb-6 leading-[1.1]"
        >
          9亿用户的
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-neon-blue via-purple-500 to-neon-pink glow-text">
            流量金矿
          </span>
          <br />
          无需下载，即刻变现
        </motion.h1>

        {/* Subtitle */}
        <motion.p
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, ease: "easeOut", delay: 0.5 }}
          className="text-gray-400 text-lg md:text-xl max-w-2xl mx-auto mb-10 leading-relaxed"
        >
          错过移动互联网，不要再错过 TON 生态。我们为您打造原生级体验的 <span className="text-white font-bold">Telegram Mini App</span>，打通 <span className="text-neon-green">社交裂变</span> + <span className="text-neon-blue">支付闭环</span> + <span className="text-neon-purple">Web3 资产</span>。
        </motion.p>

        {/* Tags */}
        <motion.div
          variants={{
            hidden: { opacity: 0 },
            show: {
              opacity: 1,
              transition: {
                staggerChildren: 0.2,
                delayChildren: 1.2
              }
            }
          }}
          initial="hidden"
          animate="show"
          className="flex flex-wrap justify-center gap-4 mb-12"
        >
          {[
            { icon: Zap, text: "无需下载" },
            { icon: Sparkles, text: "支付原子化" },
            { icon: ArrowRight, text: "病毒式裂变" },
            { icon: ShieldCheck, text: "100% 源码交付" }
          ].map((item, index) => (
            <motion.div 
              key={index}
              variants={{
                hidden: { opacity: 0, scale: 0.8, y: 20 },
                show: { 
                  opacity: 1, 
                  scale: 1, 
                  y: 0,
                  transition: { type: "spring", stiffness: 100, damping: 15 }
                }
              }}
              className="flex items-center gap-2 px-4 py-2 bg-dark-card border border-dark-border rounded-lg text-sm text-gray-300"
            >
              <item.icon className="w-4 h-4 text-neon-blue" />
              {item.text}
            </motion.div>
          ))}
        </motion.div>

        {/* CTAs */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 2.0 }}
          className="flex flex-col sm:flex-row items-center justify-center gap-4"
        >
          <button className="w-full sm:w-auto px-8 py-4 bg-gradient-to-r from-neon-blue to-neon-purple text-white font-bold rounded-lg hover:shadow-[0_0_20px_rgba(188,19,254,0.5)] transition-all duration-300 transform hover:-translate-y-1">
            立即评估我的项目方案
          </button>
          <button className="w-full sm:w-auto px-8 py-4 bg-transparent border border-white/20 text-white font-bold rounded-lg hover:bg-white/10 hover:border-white/40 transition-all duration-300">
            查看演示 Demo
          </button>
        </motion.div>

      </div>
    </section>
  );
};

export default Hero;
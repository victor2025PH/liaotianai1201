import React, { useEffect, useRef, useState } from 'react';
import { motion } from 'framer-motion';
import { Button } from './ui/Button';
import { Smartphone, Network } from 'lucide-react';
import { useLanguage } from '../contexts/LanguageContext';
import { useAIChat } from '../contexts/AIChatContext';

// Internal Component for Dynamic Stats with Particles
const DynamicStat = ({ 
  label, 
  unit, 
  colorRGB, 
  textColorClass, 
  min, 
  max, 
  isFloat = false,
  updateInterval = 2000 
}: { 
  label: string; 
  unit: string; 
  colorRGB: string; // Format: "R, G, B"
  textColorClass: string; 
  min: number; 
  max: number; 
  isFloat?: boolean;
  updateInterval?: number;
}) => {
  const [value, setValue] = useState<string | number>(min);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  // 1. Value Update Logic
  useEffect(() => {
    const updateValue = () => {
      const range = max - min;
      const randomOffset = Math.random() * range;
      const newValue = min + randomOffset;
      
      if (isFloat) {
        setValue(newValue.toFixed(2));
      } else {
        setValue(Math.floor(newValue).toLocaleString());
      }
    };

    updateValue(); // Initial set
    const interval = setInterval(updateValue, updateInterval);
    return () => clearInterval(interval);
  }, [min, max, isFloat, updateInterval]);

  // 2. Particle System Logic
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animationFrameId: number;
    const particles: {x: number, y: number, vy: number, alpha: number, size: number}[] = [];

    const render = () => {
      if (canvas.width !== canvas.offsetWidth || canvas.height !== canvas.offsetHeight) {
        canvas.width = canvas.offsetWidth;
        canvas.height = canvas.offsetHeight;
      }

      ctx.clearRect(0, 0, canvas.width, canvas.height);

      // Spawn new particles randomly
      if (Math.random() < 0.15) {
        particles.push({
          x: Math.random() * canvas.width,
          y: canvas.height, // Start from bottom
          vy: 0.5 + Math.random() * 1.5, // Velocity Y
          alpha: 1,
          size: 1 + Math.random() * 2
        });
      }

      // Update and draw particles
      ctx.fillStyle = `rgb(${colorRGB})`;
      
      for (let i = particles.length - 1; i >= 0; i--) {
        const p = particles[i];
        p.y -= p.vy;
        p.alpha -= 0.015; // Fade out
        
        if (p.alpha <= 0) {
          particles.splice(i, 1);
          continue;
        }

        ctx.globalAlpha = p.alpha;
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
        ctx.fill();
      }
      ctx.globalAlpha = 1;

      animationFrameId = requestAnimationFrame(render);
    };

    render();
    return () => cancelAnimationFrame(animationFrameId);
  }, [colorRGB]);

  return (
    <div className="relative p-4 overflow-hidden rounded-lg group hover:bg-white/5 transition-colors duration-500">
      <canvas ref={canvasRef} className="absolute inset-0 w-full h-full pointer-events-none opacity-40 group-hover:opacity-60 transition-opacity" />
      <div className="relative z-10">
        <div className="text-3xl font-mono font-bold text-white flex justify-center items-baseline gap-1 drop-shadow-md">
          {value}
          <span className={`${textColorClass} text-sm font-bold opacity-80`}>{unit}</span>
        </div>
        <div className="text-[10px] uppercase tracking-widest text-zinc-500 group-hover:text-zinc-300 transition-colors mt-1">
          {label}
        </div>
      </div>
      {/* Bottom glowing line */}
      <div 
        className="absolute bottom-0 left-0 h-[2px] w-full opacity-30 group-hover:opacity-80 transition-opacity duration-500"
        style={{ background: `linear-gradient(90deg, transparent, rgb(${colorRGB}), transparent)` }} 
      />
    </div>
  );
};

export const Hero: React.FC = () => {
  const { t } = useLanguage();
  const { openChat } = useAIChat();

  return (
    <section className="relative min-h-screen flex items-center justify-center pt-20 overflow-hidden">
      
      {/* Decorative background elements that aren't canvas */}
      <div className="absolute top-1/4 -left-20 w-96 h-96 bg-cyan-500/10 rounded-full blur-[120px]" />
      <div className="absolute bottom-1/4 -right-20 w-96 h-96 bg-purple-500/10 rounded-full blur-[120px]" />

      {/* Continuous Wave Animation Background */}
      <div className="absolute inset-0 pointer-events-none z-0 overflow-hidden">
        {/* Wave 1 - Cyan tint - Moving Left */}
        <motion.div 
          className="absolute top-[45%] left-0 w-[200%] h-32 opacity-20"
          animate={{ x: ["0%", "-50%"] }}
          transition={{ 
            duration: 25, 
            ease: "linear", 
            repeat: Infinity,
            repeatType: "loop"
          }}
        >
           <svg className="w-full h-full" viewBox="0 0 1200 120" preserveAspectRatio="none">
             <path d="M0,0V46.29c47.79,22.2,103.59,32.17,158,28,70.36-5.37,136.33-33.31,206.8-37.5C438.64,32.43,512.34,53.67,583,72.05c69.27,18,138.3,24.88,209.4,13.08,36.15-6,69.85-17.84,104.45-29.34C989.49,25,1113-14.29,1200,52.47V0Z" 
                   fill="url(#wave-grad-1)" transform="scale(1, -1) translate(0, -120)" opacity="0.3"></path>
             <path d="M0,0V15.81C13,36.92,27.64,56.86,47.69,72.05,99.41,111.27,165,111,224.58,91.58c31.15-10.15,60.09-26.07,89.67-39.8,40.92-19,84.73-46,130.83-49.67,36.26-2.85,70.9,9.42,98.6,31.56,31.77,25.39,62.32,62,103.63,73,40.44,10.79,81.35-6.69,119.13-24.28s75.16-39,116.92-43.05c59.73-5.85,113.28,22.88,168.9,38.84,30.2,8.66,59,6.17,87.09-7.5,22.43-10.89,48-26.93,60.65-49.24V0Z" 
                   fill="url(#wave-grad-1)" opacity="0.5"></path>
              <defs>
                <linearGradient id="wave-grad-1" x1="0%" y1="0%" x2="100%" y2="0%">
                  <stop offset="0%" stopColor="rgba(6,182,212,0)" />
                  <stop offset="50%" stopColor="rgba(6,182,212,0.3)" />
                  <stop offset="100%" stopColor="rgba(6,182,212,0)" />
                </linearGradient>
              </defs>
           </svg>
        </motion.div>

        {/* Wave 2 - Purple tint - Moving Right */}
        <motion.div 
          className="absolute top-[55%] left-0 w-[200%] h-32 opacity-20"
          animate={{ x: ["-50%", "0%"] }}
          transition={{ 
            duration: 20, 
            ease: "linear", 
            repeat: Infinity,
            repeatType: "loop"
          }}
        >
           <svg className="w-full h-full" viewBox="0 0 1200 120" preserveAspectRatio="none">
             <path d="M321.39,56.44c58-10.79,114.16-30.13,172-41.86,82.39-16.72,168.19-17.73,250.45-.39C823.78,31,906.67,72,985.66,92.83c70.05,18.48,146.53,26.09,214.34,3V0H0V27.35A600.21,600.21,0,0,0,321.39,56.44Z" 
                   fill="url(#wave-grad-2)"></path>
              <defs>
                <linearGradient id="wave-grad-2" x1="0%" y1="0%" x2="100%" y2="0%">
                  <stop offset="0%" stopColor="rgba(168,85,247,0)" />
                  <stop offset="50%" stopColor="rgba(168,85,247,0.3)" />
                  <stop offset="100%" stopColor="rgba(168,85,247,0)" />
                </linearGradient>
              </defs>
           </svg>
        </motion.div>
      </div>

      <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
        
        {/* Top Tag */}
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/5 border border-white/10 mb-8 animate-fade-in-up">
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
          </span>
          <span className="font-mono text-xs text-zinc-400 tracking-widest uppercase">
            {t('hero.status')}
          </span>
        </div>

        {/* Main Headline */}
        <h1 className="text-4xl md:text-6xl lg:text-8xl font-bold tracking-tighter text-white mb-6 leading-tight">
          <span className="block text-transparent bg-clip-text bg-gradient-to-b from-white to-zinc-400">
            {t('hero.headline_1')}
          </span>
          <span className="block text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-purple-500 animate-pulse-slow pb-2">
            {t('hero.headline_2')}
          </span>
        </h1>

        {/* Subtitle */}
        <h2 className="text-lg md:text-xl lg:text-2xl text-cyan-500 font-mono mb-6 tracking-wide uppercase">
          {t('hero.subtitle')}
        </h2>

        {/* Description */}
        <p className="max-w-3xl mx-auto text-lg md:text-xl text-zinc-400 mb-10 font-light leading-relaxed">
          {t('hero.description')}
        </p>

        {/* Dynamic Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-2xl mx-auto mb-12 border-y border-white/5 py-8 backdrop-blur-sm bg-black/20">
          
          {/* Active Nodes - Cyan */}
          <DynamicStat 
            label={t('hero.stat_nodes')} 
            unit="+" 
            colorRGB="0, 255, 255" 
            textColorClass="text-cyan-500"
            min={5100}
            max={5400}
            updateInterval={3000}
          />
          
          {/* Ops/Sec - Purple */}
          <div className="md:border-x border-white/5">
            <DynamicStat 
              label={t('hero.stat_ops')} 
              unit="k" 
              colorRGB="168, 85, 247" 
              textColorClass="text-purple-500"
              min={92}
              max={99}
              isFloat={true}
              updateInterval={1500}
            />
          </div>
          
          {/* Uptime - Green (Fluctuating 80-98%) */}
          <DynamicStat 
            label={t('hero.stat_time')} 
            unit="%" 
            colorRGB="34, 197, 94" 
            textColorClass="text-green-500"
            min={80}
            max={98.99}
            isFloat={true}
            updateInterval={800} // Faster fluctuation for "live" feel
          />
          
        </div>

        {/* CTAs */}
        <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
          <Button 
            variant="primary" 
            icon 
            onClick={(e) => openChat("用户请求启动接管程序。", "正在初始化接管序列...\n\n我是系统核心。您希望主宰哪个领域？\n\n- 社交媒体流量\n- 设备控制\n- 语音网络", e.currentTarget)}
          >
            {t('hero.btn_deploy')}
          </Button>
          <Button 
            variant="secondary"
            onClick={(e) => openChat("用户请求查看架构蓝图。", "正在访问蓝图...\n\n显示节点拓扑图。\n\n我们的系统基于去中心化网状网络。您需要技术规格还是收入预测？", e.currentTarget)}
          >
            {t('hero.btn_view')}
          </Button>
        </div>

      </div>

      {/* Bottom fade */}
      <div className="absolute bottom-0 left-0 w-full h-24 bg-gradient-to-t from-zinc-950 to-transparent z-20 pointer-events-none" />
    </section>
  );
};
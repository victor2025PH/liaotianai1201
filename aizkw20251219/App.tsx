import React, { useRef, useState, useEffect } from 'react';
import { motion, useScroll, useTransform, useSpring, AnimatePresence } from 'framer-motion';
import { HashRouter, Routes, Route, Link } from 'react-router-dom';
import { Navbar } from './components/Navbar';
import { Hero } from './components/Hero';
import { Background } from './components/Background';
import { Section } from './components/Section';
import { Button } from './components/ui/Button';
import { Smartphone, Mic, MessageSquare, Phone, Server, Radio, MessagesSquare, Quote, Shield, Cpu, Globe, Zap, Calendar, Mail, ArrowLeft, Linkedin, Twitter, X, BarChart3, Users, Clock, Activity, ArrowDown, Send, MessageCircle, Facebook, CreditCard, DollarSign, PenTool } from 'lucide-react';
import { useLanguage } from './contexts/LanguageContext';
import { AIChatProvider, useAIChat } from './contexts/AIChatContext';
import { AIChatTerminal } from './components/AIChatTerminal';
import { Matrix3DScene } from './components/Matrix3DScene';
import { PricingSection } from './components/PricingSection';
import { AISprite } from './components/AISprite';
import { config } from './src/config';

// --- Brand Icons Components ---
const TelegramIcon = ({ className }: { className?: string }) => (
  <svg viewBox="0 0 24 24" fill="currentColor" className={className}>
    <path d="M11.944 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0a12 12 0 0 0-.056 0zm4.962 7.224c.1-.002.321.023.465.14a.506.506 0 0 1 .171.325c.016.093.036.306.02.472-.18 1.898-.962 6.502-1.36 8.627-.168.9-.499 1.201-.82 1.23-.696.065-1.225-.46-1.9-.902-1.056-.693-1.653-1.124-2.678-1.8-1.185-.78-.417-1.21.258-1.91.177-.184 3.247-2.977 3.307-3.23.007-.032.014-.15-.056-.212s-.174-.041-.249-.024c-.106.024-1.793 1.14-5.061 3.345-.48.33-.913.49-1.302.48-.428-.008-1.252-.241-1.865-.44-.752-.245-1.349-.374-1.297-.789.027-.216.325-.437.893-.663 3.498-1.524 5.83-2.529 6.998-3.014 3.332-1.386 4.025-1.627 4.476-1.635z" />
  </svg>
);

const WhatsAppIcon = ({ className }: { className?: string }) => (
  <svg viewBox="0 0 24 24" fill="currentColor" className={className}>
    <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 0 1-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 0 1-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 0 1 2.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0 0 12.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 0 0 5.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 0 0-3.48-8.413Z" />
  </svg>
);

const TikTokIcon = ({ className }: { className?: string }) => (
  <svg viewBox="0 0 24 24" fill="currentColor" className={className}>
    <path d="M12.588 0C12.553.005 12.523 0 12.486 0H8.086c-.46 0-.853.33-.92.784-.012.08-.018.16-.018.243v14.473c0 2.227-1.769 4.029-3.951 4.029-2.182 0-3.951-1.802-3.951-4.029 0-2.227 1.769-4.029 3.951-4.029.289 0 .57.032.842.091.439.096.885-.157 1.026-.583.053-.162.081-.334.081-.51V6.627c0-.528-.396-.967-.917-1.018-.34-.033-.687-.05-1.033-.05C5.816 5.559 0 11.482 0 18.788c0 2.876 2.292 5.212 5.115 5.212 2.823 0 5.115-2.336 5.115-5.212V7.796c2.518 1.838 4.048 4.793 4.048 8.114 0 .553.448 1 1 1h4.068c.552 0 1-.447 1-1 0-7.391-5.55-13.486-12.636-13.91l-.122-.007z" />
  </svg>
);

const XiaoHongShuIcon = ({ className }: { className?: string }) => (
    <svg viewBox="0 0 24 24" fill="currentColor" className={className}>
        <path d="M4 0H20C22.2 0 24 1.8 24 4V20C24 22.2 22.2 24 20 24H4C1.8 24 0 22.2 0 20V4C0 1.8 1.8 0 4 0ZM18.5 7.5C18.5 7.5 16.5 7.5 16.5 9.5C16.5 11.5 17.5 12 18.5 12C19.5 12 20.5 11.5 20.5 9.5C20.5 7.5 18.5 7.5 18.5 7.5ZM5.5 7.5C5.5 7.5 3.5 7.5 3.5 9.5C3.5 11.5 4.5 12 5.5 12C6.5 12 7.5 11.5 7.5 9.5C7.5 7.5 5.5 7.5 5.5 7.5ZM12 4C8.5 4 6 6.5 6 10V14C6 17.5 8.5 20 12 20C15.5 20 18 17.5 18 14V10C18 6.5 15.5 4 12 4ZM12 17C10 17 9 16 9 14V11C9 9 10 8 12 8C14 8 15 9 15 11V14C15 16 14 17 12 17Z" />
    </svg>
);

const GmailIcon = ({ className }: { className?: string }) => (
  <svg viewBox="0 0 24 24" fill="currentColor" className={className}>
    <path d="M24 5.457v13.909c0 .904-.732 1.636-1.636 1.636h-3.819V11.73L12 16.64l-6.545-4.91v9.273H1.636A1.636 1.636 0 0 1 0 19.366V5.457c0-2.023 2.309-3.178 3.927-1.964L5.455 4.64 12 9.548l6.545-4.91 1.528-1.145C21.69 2.28 24 3.434 24 5.457z" />
  </svg>
);

// --- Component: Data Flow Connector ---
const DataFlowConnector: React.FC<{ direction?: 'right' | 'down' }> = ({ direction = 'right' }) => {
    return (
        <div className={`absolute pointer-events-none z-0 flex items-center justify-center 
            ${direction === 'right' 
                ? 'right-[-32px] top-1/2 -translate-y-1/2 w-8 h-full hidden lg:flex' 
                : 'bottom-[-32px] left-1/2 -translate-x-1/2 h-8 w-full flex lg:hidden'
            }`
        }>
            {direction === 'right' ? (
                // Horizontal Flow (Desktop)
                <div className="relative w-full h-8 flex items-center">
                     {/* Static Line */}
                     <div className="w-full h-[2px] bg-zinc-800"></div>
                     {/* Moving Pulse */}
                     <motion.div 
                        className="absolute h-[4px] w-8 bg-cyan-500 rounded-full shadow-[0_0_10px_#00FFFF]"
                        animate={{ x: [-20, 40], opacity: [0, 1, 0] }}
                        transition={{ duration: 1.5, repeat: Infinity, ease: "linear" }}
                     />
                     <div className="absolute right-0 text-cyan-500/50">
                        <ArrowDown className="-rotate-90 w-4 h-4" />
                     </div>
                </div>
            ) : (
                // Vertical Flow (Mobile)
                <div className="relative h-full w-8 flex flex-col items-center justify-center">
                     {/* Static Line */}
                     <div className="h-full w-[2px] bg-zinc-800"></div>
                     {/* Moving Pulse */}
                     <motion.div 
                        className="absolute w-[4px] h-8 bg-cyan-500 rounded-full shadow-[0_0_10px_#00FFFF]"
                        animate={{ y: [-20, 40], opacity: [0, 1, 0] }}
                        transition={{ duration: 1.5, repeat: Infinity, ease: "linear" }}
                     />
                     <div className="absolute bottom-0 text-cyan-500/50">
                        <ArrowDown className="w-4 h-4" />
                     </div>
                </div>
            )}
        </div>
    );
};

const ContactModal: React.FC<{ isOpen: boolean; onClose: () => void }> = ({ isOpen, onClose }) => {
  const { t } = useLanguage();
  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
          <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="absolute inset-0 bg-black/80 backdrop-blur-sm"
          />
          <motion.div 
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            className="relative w-full max-w-lg glass-panel p-8 rounded-2xl border border-cyan-500/30 shadow-[0_0_50px_rgba(0,255,255,0.2)]"
          >
            <button 
              onClick={onClose} 
              className="absolute top-4 right-4 text-zinc-400 hover:text-white transition-colors p-2 hover:bg-white/10 rounded-full"
            >
              <X className="w-5 h-5" />
            </button>
            
            <div className="text-center mb-8">
              <h3 className="text-2xl font-bold text-white mb-2 font-mono uppercase tracking-wider text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-white">
                {t('contact.title')}
              </h3>
              <p className="text-zinc-400 font-light">
                {t('contact.subtitle')}
              </p>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Telegram */}
              <a href={config.contact.telegram} target="_blank" rel="noopener noreferrer" data-robot-avoid="true" className="flex items-center gap-4 p-4 rounded-xl bg-white/5 border border-white/10 hover:border-[#229ED9] hover:bg-[#229ED9]/10 transition-all group hover:scale-[1.02] active:scale-[0.98]">
                <div className="p-3 rounded-full bg-white/5 group-hover:bg-[#229ED9]/20 transition-colors">
                  <TelegramIcon className="w-6 h-6 text-zinc-400 group-hover:text-[#229ED9]" />
                </div>
                <div className="text-left">
                  <div className="text-white font-bold group-hover:text-[#229ED9] font-mono">{t('contact.telegram')}</div>
                  <div className="text-[10px] text-zinc-500 uppercase tracking-wider">{t('contact.telegram_desc')}</div>
                </div>
              </a>

              {/* WhatsApp */}
              <a href={config.contact.whatsapp} target="_blank" rel="noopener noreferrer" data-robot-avoid="true" className="flex items-center gap-4 p-4 rounded-xl bg-white/5 border border-white/10 hover:border-[#25D366] hover:bg-[#25D366]/10 transition-all group hover:scale-[1.02] active:scale-[0.98]">
                <div className="p-3 rounded-full bg-white/5 group-hover:bg-[#25D366]/20 transition-colors">
                  <WhatsAppIcon className="w-6 h-6 text-zinc-400 group-hover:text-[#25D366]" />
                </div>
                <div className="text-left">
                  <div className="text-white font-bold group-hover:text-[#25D366] font-mono">{t('contact.whatsapp')}</div>
                  <div className="text-[10px] text-zinc-500 uppercase tracking-wider">{t('contact.whatsapp_desc')}</div>
                </div>
              </a>

              {/* WhatsApp (原 LinkedIn 位置) */}
              <a href={config.contact.whatsapp} target="_blank" rel="noopener noreferrer" data-robot-avoid="true" className="flex items-center gap-4 p-4 rounded-xl bg-white/5 border border-white/10 hover:border-[#25D366] hover:bg-[#25D366]/10 transition-all group hover:scale-[1.02] active:scale-[0.98]">
                <div className="p-3 rounded-full bg-white/5 group-hover:bg-[#25D366]/20 transition-colors">
                  <WhatsAppIcon className="w-6 h-6 text-zinc-400 group-hover:text-[#25D366]" />
                </div>
                <div className="text-left">
                  <div className="text-white font-bold group-hover:text-[#25D366] font-mono">{t('contact.whatsapp')}</div>
                  <div className="text-[10px] text-zinc-500 uppercase tracking-wider">{t('contact.whatsapp_desc')}</div>
                </div>
              </a>

              {/* Gmail */}
              <a href={`mailto:${config.contact.email}`} data-robot-avoid="true" className="flex items-center gap-4 p-4 rounded-xl bg-white/5 border border-white/10 hover:border-[#EA4335] hover:bg-[#EA4335]/10 transition-all group hover:scale-[1.02] active:scale-[0.98]">
                <div className="p-3 rounded-full bg-white/5 group-hover:bg-[#EA4335]/20 transition-colors">
                  <GmailIcon className="w-6 h-6 text-zinc-400 group-hover:text-[#EA4335]" />
                </div>
                <div className="text-left">
                  <div className="text-white font-bold group-hover:text-[#EA4335] font-mono">{t('contact.gmail')}</div>
                  <div className="text-[10px] text-zinc-500 uppercase tracking-wider">{t('contact.gmail_desc')}</div>
                </div>
              </a>
            </div>
            
             <div className="mt-8 pt-6 border-t border-white/5 text-center">
               <p className="text-[10px] text-zinc-600 font-mono">
                 {t('contact.id')}: {Math.random().toString(36).substring(7).toUpperCase()}
               </p>
             </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
};

// --- Service Detail Modal ---
const ServiceModal: React.FC<{ 
  isOpen: boolean; 
  onClose: () => void; 
  feature: { title: string; desc: string; theme: string } | null;
}> = ({ isOpen, onClose, feature }) => {
  const { t } = useLanguage();
  const { openChat } = useAIChat();

  if (!isOpen || !feature) return null;

  // Retrieve detailed description from context based on the title (which acts as the tag key here)
  // Fallback to the passed 'desc' if specific translation isn't found
  const detailKey = `capabilities.tag_details.${feature.title}`;
  const detailedDesc = t(detailKey) !== detailKey ? t(detailKey) : feature.desc;

  // Dynamic Styles
  const themeColors: Record<string, string> = {
    cyan: 'border-cyan-500/50 shadow-[0_0_50px_rgba(0,255,255,0.2)] text-cyan-400',
    green: 'border-green-500/50 shadow-[0_0_50px_rgba(34,197,94,0.2)] text-green-400',
    pink: 'border-pink-500/50 shadow-[0_0_50px_rgba(236,72,153,0.2)] text-pink-400',
    red: 'border-red-500/50 shadow-[0_0_50px_rgba(239,68,68,0.2)] text-red-400',
    blue: 'border-blue-500/50 shadow-[0_0_50px_rgba(59,130,246,0.2)] text-blue-400',
    purple: 'border-purple-500/50 shadow-[0_0_50px_rgba(168,85,247,0.2)] text-purple-400',
    yellow: 'border-yellow-500/50 shadow-[0_0_50px_rgba(234,179,8,0.2)] text-yellow-400',
    orange: 'border-orange-500/50 shadow-[0_0_50px_rgba(249,115,22,0.2)] text-orange-400',
    indigo: 'border-indigo-500/50 shadow-[0_0_50px_rgba(99,102,241,0.2)] text-indigo-400',
  };
  const activeStyle = themeColors[feature.theme] || themeColors.cyan;

  // Trigger Chat Logic
  const handleConsult = (type: 'price' | 'content' | 'results') => {
      onClose(); // Close modal first
      
      let prompt = "";
      if (type === 'price') {
          prompt = `用户询问 [${feature.title}] 模块的价格与部署成本。请提供详细报价方案。`;
      } else if (type === 'content') {
          prompt = `用户希望优化 [${feature.title}] 模块的发送内容。请询问目标受众，并给出高转化文案建议。`;
      } else if (type === 'results') {
          prompt = `用户想查看 [${feature.title}] 模块的预期效果数据（ROI, 点击率, 到达率）。请模拟展示真实案例数据。`;
      }
      
      openChat(`Module Context: ${feature.title}`, prompt);
  };

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
        <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="absolute inset-0 bg-black/90 backdrop-blur-md"
        />
        <motion.div
            initial={{ opacity: 0, scale: 0.9, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.9, y: 20 }}
            className={`relative w-full max-w-lg bg-zinc-950 p-8 rounded-2xl border-2 ${activeStyle} flex flex-col`}
        >
             <button
              onClick={onClose}
              className="absolute top-4 right-4 text-zinc-400 hover:text-white transition-colors p-2 hover:bg-white/10 rounded-full"
            >
              <X className="w-5 h-5" />
            </button>
            
            <div className="mb-6 flex items-center gap-3">
               <div className={`p-2 rounded-lg bg-white/5 border border-white/10 ${activeStyle.split(' ')[2]}`}>
                  <Zap className="w-6 h-6" />
               </div>
               <h3 className={`text-2xl font-bold font-mono tracking-wide ${activeStyle.split(' ')[2]}`}>
                 {feature.title}
               </h3>
            </div>

            <div className="text-zinc-200 text-lg leading-relaxed font-light border-t border-white/10 pt-6 min-h-[100px]">
                {detailedDesc}
            </div>

            <div className="mt-8 grid grid-cols-3 gap-3">
                <button 
                    onClick={() => handleConsult('price')}
                    className="flex flex-col items-center justify-center gap-2 p-3 rounded bg-zinc-900 border border-zinc-800 hover:border-cyan-500/50 hover:bg-cyan-950/30 transition-all group"
                >
                    <DollarSign className="w-5 h-5 text-zinc-500 group-hover:text-cyan-400 transition-colors" />
                    <span className="text-[10px] uppercase font-bold text-zinc-400 group-hover:text-white">{t('capabilities.modal_price')}</span>
                </button>
                <button 
                    onClick={() => handleConsult('content')}
                    className="flex flex-col items-center justify-center gap-2 p-3 rounded bg-zinc-900 border border-zinc-800 hover:border-purple-500/50 hover:bg-purple-950/30 transition-all group"
                >
                    <PenTool className="w-5 h-5 text-zinc-500 group-hover:text-purple-400 transition-colors" />
                    <span className="text-[10px] uppercase font-bold text-zinc-400 group-hover:text-white">{t('capabilities.modal_content')}</span>
                </button>
                <button 
                    onClick={() => handleConsult('results')}
                    className="flex flex-col items-center justify-center gap-2 p-3 rounded bg-zinc-900 border border-zinc-800 hover:border-green-500/50 hover:bg-green-950/30 transition-all group"
                >
                    <BarChart3 className="w-5 h-5 text-zinc-500 group-hover:text-green-400 transition-colors" />
                    <span className="text-[10px] uppercase font-bold text-zinc-400 group-hover:text-white">{t('capabilities.modal_results')}</span>
                </button>
            </div>

            <div className="mt-6 pt-4 border-t border-white/10 flex justify-between items-center">
               <span className="text-[10px] text-zinc-500 font-mono uppercase tracking-widest">AI Agent Online</span>
               <div className="flex gap-2">
                  <div className="w-2 h-2 rounded-full bg-zinc-700 animate-pulse" />
                  <div className="w-2 h-2 rounded-full bg-zinc-700 animate-pulse delay-75" />
                  <div className="w-2 h-2 rounded-full bg-zinc-700 animate-pulse delay-150" />
               </div>
            </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
};

const SystemDetails: React.FC = () => {
  const [logoError, setLogoError] = useState(false);
  const { t } = useLanguage();

  return (
    <div className="min-h-screen bg-black flex flex-col items-center justify-center p-4 relative overflow-hidden">
       {/* Background elements */}
       <div className="absolute inset-0 pointer-events-none opacity-20 bg-[url('https://grainy-gradients.vercel.app/noise.svg')]"></div>
       <div className="absolute top-0 w-full h-1 bg-gradient-to-r from-transparent via-cyan-500 to-transparent opacity-50"></div>
       
       <div className="relative z-10 flex flex-col items-center gap-6">
         <div className="w-20 h-20 flex items-center justify-center animate-pulse">
            {!logoError ? (
              <img 
                src="/logo.png" 
                alt="System" 
                onError={() => setLogoError(true)}
                className="w-full h-full object-contain" 
              />
            ) : (
              <div className="w-full h-full p-2 bg-cyan-500/10 rounded-full border border-cyan-500/50 flex items-center justify-center shadow-[0_0_15px_rgba(0,255,255,0.4)]">
                 <Shield className="w-10 h-10 text-cyan-500" />
              </div>
            )}
         </div>
         
         <div className="font-mono text-cyan-500 text-xl tracking-widest animate-pulse text-center uppercase">
           System details loading...
         </div>
         
         <div className="w-64 h-1 bg-zinc-800 rounded-full overflow-hidden relative">
           <div className="absolute inset-0 bg-cyan-500 animate-shimmer"></div>
         </div>
         
         <div className="font-mono text-xs text-zinc-500">
           {t('nav.system_id')}: 8492-AX
         </div>
         
         <Link to="/" className="mt-8 flex items-center gap-2 text-zinc-400 hover:text-white transition-colors font-mono text-xs uppercase tracking-wider group">
           <ArrowLeft className="w-4 h-4 group-hover:-translate-x-1 transition-transform" />
           {t('nav.contact').replace('Us', '')} Back
         </Link>
       </div>
    </div>
  );
};

const PSYCH_QUOTES = [
  {
    id: 1,
    text: "当您的竞争对手还在手动回复信息、为招聘销售发愁时，您的系统已经完成了第一万次自动成交。这不是竞争，这是维度的超越。",
    author: "SYSTEM OVERLORD"
  },
  {
    id: 2,
    text: "真正的自由不是逃避工作，而是拥有无需在场也能自行运转的印钞机。让算法成为您最忠诚的猎手，24小时不知疲倦地为您捕获价值。",
    author: "PASSIVE INCOME PROTOCOL"
  },
  {
    id: 3,
    text: "在这个赢家通吃的数字时代，速度就是一切。人类的反应是毫秒级，而您的矩阵是纳秒级。不要试图用血肉之躯去对抗硅基生命的速度。",
    author: "SILICON SUPREMACY"
  },
  {
    id: 4,
    text: "平庸的企业通过堆砌人力来寻求增长，伟大的领袖通过构建系统来统治市场。您是在经营一家公司，还是在指挥一支数字化军团？",
    author: "COMMANDER MODULE"
  }
];

const LandingContent: React.FC = () => {
  const { t } = useLanguage();
  const [showContactModal, setShowContactModal] = useState(false);
  const [activeFeature, setActiveFeature] = useState<{ title: string; desc: string; theme: string } | null>(null);
  const { openChat } = useAIChat();
  
  // Rotating Quote Logic
  const [currentQuoteIndex, setCurrentQuoteIndex] = useState(0);
  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentQuoteIndex((prev) => (prev + 1) % PSYCH_QUOTES.length);
    }, 6000); // Rotate every 6 seconds
    return () => clearInterval(interval);
  }, []);

  // --- Scroll Animation Logic ---
  const trustRef = useRef(null);
  const { scrollYProgress: trustScroll } = useScroll({
    target: trustRef,
    offset: ["start end", "end start"]
  });
  const trustSpring = useSpring(trustScroll, { stiffness: 50, damping: 20 });
  const tY1 = useTransform(trustSpring, [0, 1], [0, -40]);
  const tY2 = useTransform(trustSpring, [0, 1], [60, -60]); 
  const tY3 = useTransform(trustSpring, [0, 1], [0, -40]);

  const matrixRef = useRef(null);
  const { scrollYProgress: matrixProgress } = useScroll({
    target: matrixRef,
    offset: ["start end", "end start"]
  });
  const matrixScale = useTransform(matrixProgress, [0, 0.5], [0.9, 1]);
  const matrixOpacity = useTransform(matrixProgress, [0, 0.3], [0, 1]);

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.15,
        delayChildren: 0.1
      }
    }
  };

  const cardVariants = {
    hidden: { y: 60, opacity: 0, scale: 0.95, rotateX: 10 },
    visible: { 
      y: 0, 
      opacity: 1, 
      scale: 1, 
      rotateX: 0,
      transition: {
        type: "spring" as const,
        stiffness: 60,
        damping: 12
      }
    }
  };

  const partners = [
    { name: t('trust.p1'), icon: Cpu },
    { name: t('trust.p2'), icon: Zap },
    { name: t('trust.p3'), icon: Globe },
    { name: t('trust.p4'), icon: Shield }
  ];

  // Specific Capabilities Data for 9 Cards with Visual Themes
  const capabilities = [
    { 
      id: 'c1', 
      icon: TelegramIcon, 
      theme: 'cyan',
      color: 'text-cyan-400', 
      border: 'border-cyan-500/50', 
      shadow: 'shadow-[0_0_30px_-5px_rgba(6,182,212,0.3)]',
      bg: 'bg-cyan-950/20', 
      hoverLine: 'bg-cyan-500', 
      chatContext: 'Telegram Matrix' 
    },
    { 
      id: 'c2', 
      icon: WhatsAppIcon, 
      theme: 'green',
      color: 'text-green-400', 
      border: 'border-green-500/50', 
      shadow: 'shadow-[0_0_30px_-5px_rgba(34,197,94,0.3)]',
      bg: 'bg-green-950/20', 
      hoverLine: 'bg-green-500', 
      chatContext: 'WhatsApp Marketing' 
    },
    { 
      id: 'c3', 
      icon: TikTokIcon, 
      theme: 'pink',
      color: 'text-pink-400', 
      border: 'border-pink-500/50', 
      shadow: 'shadow-[0_0_30px_-5px_rgba(236,72,153,0.3)]',
      bg: 'bg-pink-950/20', 
      hoverLine: 'bg-pink-500', 
      chatContext: 'TikTok Matrix' 
    },
    { 
      id: 'c4', 
      icon: XiaoHongShuIcon, 
      theme: 'red', 
      color: 'text-red-400', 
      border: 'border-red-500/50', 
      shadow: 'shadow-[0_0_30px_-5px_rgba(239,68,68,0.3)]',
      bg: 'bg-red-950/20', 
      hoverLine: 'bg-red-500', 
      chatContext: 'RedNote Seeding' 
    },
    { 
      id: 'c5', 
      icon: Facebook, 
      theme: 'blue', 
      color: 'text-blue-400', 
      border: 'border-blue-500/50', 
      shadow: 'shadow-[0_0_30px_-5px_rgba(59,130,246,0.3)]',
      bg: 'bg-blue-950/20', 
      hoverLine: 'bg-blue-500', 
      chatContext: 'Facebook Ads' 
    },
    { 
      id: 'c6', 
      icon: Smartphone, 
      theme: 'purple', 
      color: 'text-purple-400', 
      border: 'border-purple-500/50', 
      shadow: 'shadow-[0_0_30px_-5px_rgba(168,85,247,0.3)]',
      bg: 'bg-purple-950/20', 
      hoverLine: 'bg-purple-500', 
      chatContext: 'Cloud Infrastructure' 
    },
    { 
      id: 'c7', 
      icon: CreditCard, 
      theme: 'yellow', 
      color: 'text-yellow-400', 
      border: 'border-yellow-500/50', 
      shadow: 'shadow-[0_0_30px_-5px_rgba(234,179,8,0.3)]',
      bg: 'bg-yellow-950/20', 
      hoverLine: 'bg-yellow-500', 
      chatContext: 'Global Payment' 
    },
    { 
      id: 'c8', 
      icon: MessageCircle, // Reuse MessageCircle or Mail
      theme: 'orange', 
      color: 'text-orange-400', 
      border: 'border-orange-500/50', 
      shadow: 'shadow-[0_0_30px_-5px_rgba(249,115,22,0.3)]',
      bg: 'bg-orange-950/20', 
      hoverLine: 'bg-orange-500', 
      chatContext: 'Global SMS' 
    },
    { 
      id: 'c9', 
      icon: Phone, 
      theme: 'indigo', 
      color: 'text-indigo-400', 
      border: 'border-indigo-500/50', 
      shadow: 'shadow-[0_0_30px_-5px_rgba(99,102,241,0.3)]',
      bg: 'bg-indigo-950/20', 
      hoverLine: 'bg-indigo-500', 
      chatContext: 'Voice Command' 
    },
  ];

  return (
    <div className="relative min-h-screen text-zinc-200 selection:bg-cyan-500/30 selection:text-cyan-200 font-sans bg-black">
      
      {/* Contact Modal */}
      <ContactModal isOpen={showContactModal} onClose={() => setShowContactModal(false)} />
      
      {/* Feature Detail Modal */}
      <ServiceModal 
        isOpen={!!activeFeature} 
        onClose={() => setActiveFeature(null)} 
        feature={activeFeature} 
      />
      
      {/* AI Chat Terminal */}
      <AIChatTerminal />

      {/* NEW: Interactive AI Sprite */}
      <AISprite />

      {/* Dynamic Background */}
      <Background />
      
      {/* Scanline Overlay */}
      <div className="fixed inset-0 pointer-events-none z-[1] bg-[url('https://grainy-gradients.vercel.app/noise.svg')] opacity-20 brightness-100 contrast-150"></div>
      
      {/* Navigation */}
      <Navbar />

      <main className="relative z-10">
        <Hero />

        {/* Section 1: Manifesto */}
        <Section 
            id="manifesto" 
            className="py-32" 
            variant="deep"
            divider="slant-bottom"
        >
          <div className="max-w-5xl mx-auto text-center relative">
            <div className="absolute inset-0 flex items-center justify-center pointer-events-none opacity-10">
               <h2 className="text-[12rem] md:text-[20rem] font-black text-white leading-none tracking-tighter blur-sm select-none">
                 DOMINATE
               </h2>
            </div>

            <motion.div 
              initial={{ scale: 0.9, opacity: 0 }}
              whileInView={{ scale: 1, opacity: 1 }}
              viewport={{ once: true }}
              transition={{ duration: 1, type: "spring", stiffness: 40 }}
              className="relative z-10"
            >
              <h2 className="text-2xl md:text-3xl font-mono text-cyan-500 mb-8 tracking-[0.5em] uppercase">
                {t('value.title')}
              </h2>
              
              <div className="relative min-h-[200px] flex flex-col justify-center items-center">
                <AnimatePresence mode="wait">
                  <motion.div
                    key={currentQuoteIndex}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -20 }}
                    transition={{ duration: 0.6 }}
                    className="flex flex-col gap-6"
                    style={{ 
                      filter: 'blur(0px)',
                      willChange: 'opacity, transform'
                    }}
                  >
                    <p className="text-3xl md:text-5xl font-bold text-white leading-tight">
                      "{PSYCH_QUOTES[currentQuoteIndex].text}"
                    </p>
                    <div 
                      className="flex items-center justify-center gap-4 cursor-pointer group hover:scale-105 transition-transform"
                      onClick={(e) => openChat(`User interested in quote by ${PSYCH_QUOTES[currentQuoteIndex].author}`, `Identity Verified: ${PSYCH_QUOTES[currentQuoteIndex].author}.\n\nThis core philosophy drives our entire automated architecture.\n\nWould you like to know how we apply "Silicon Supremacy" to revenue generation?`, e.currentTarget)}
                    >
                       <div className="h-px w-12 bg-cyan-500/50" />
                       <div className="flex items-center gap-2">
                         <div className="text-sm font-mono text-cyan-400 tracking-widest uppercase">
                           {PSYCH_QUOTES[currentQuoteIndex].author}
                         </div>
                         <MessageCircle className="w-3 h-3 text-cyan-500 opacity-0 group-hover:opacity-100 transition-opacity" />
                       </div>
                       <div className="h-px w-12 bg-cyan-500/50" />
                    </div>
                  </motion.div>
                </AnimatePresence>
              </div>
            </motion.div>
          </div>
        </Section>

        {/* Section 2: Matrix (System Visualizer) - MOVED UP */}
        <Section 
            id="matrix" 
            title={t('matrix.title')} 
            subtitle={t('matrix.subtitle')}
            variant="deep"
            className="pt-40" // Adjust for slant overlap from Manifesto
        >
          <div className="space-y-12" ref={matrixRef}>
             <motion.div 
               style={{ scale: matrixScale, opacity: matrixOpacity }}
               className="group relative rounded-2xl overflow-hidden border border-white/10 bg-zinc-900/50 hover:border-cyan-500/50 transition-all duration-500 will-change-transform shadow-[0_0_0_0_rgba(0,255,255,0)] hover:shadow-[0_0_40px_-10px_rgba(0,255,255,0.2)]"
             >
                 <div className="grid md:grid-cols-2 gap-0">
                    {/* Full Height Matrix Scene */}
                    <div 
                      onClick={(e) => openChat("User accessed Matrix View.", "Accessing Real-Time Monitor...\n\nThis is the digital heartbeat of your operation. Every node represents an active automated process.\n\nView node logs?", e.currentTarget)}
                      className="h-[600px] bg-zinc-950 relative overflow-hidden flex items-center justify-center cursor-pointer group/grid border-r border-white/5"
                    >
                       <Matrix3DScene />
                    </div>
                    
                    <div className="p-12 flex flex-col justify-center bg-black/80 backdrop-blur-xl relative">
                       {/* Decorative Lines */}
                       <div className="absolute top-0 right-0 w-32 h-32 border-t-2 border-r-2 border-cyan-500/20 rounded-tr-3xl pointer-events-none" />
                       <div className="absolute bottom-0 left-0 w-32 h-32 border-b-2 border-l-2 border-cyan-500/20 rounded-bl-3xl pointer-events-none" />

                       <div className="font-mono text-cyan-500 text-xs mb-6 flex items-center gap-2">
                          <span className="w-2 h-2 bg-cyan-500 rounded-full animate-pulse shadow-[0_0_10px_#00FFFF]"></span>
                          {t('matrix.active')}
                       </div>
                       
                       <h3 className="text-4xl md:text-5xl font-bold text-white mb-8 tracking-tight">
                         {t('matrix.card_title')}
                       </h3>
                       <p className="text-xl text-zinc-400 mb-10 leading-relaxed font-light">
                         {t('matrix.card_desc')}
                       </p>
                       
                       <div className="flex flex-wrap gap-3 mb-10">
                          {[t('matrix.t1'), t('matrix.t2'), t('matrix.t3'), t('matrix.t4')].map(tag => (
                            <span 
                              key={tag} 
                              onClick={(e) => {
                                e.stopPropagation();
                                openChat(`User queried component: ${tag}`, `Component Analysis: ${tag}\n\nCritical architecture module. Maintains high availability & throughput.\n\nDeploy independent instance?`, e.currentTarget)
                              }}
                              className="px-4 py-2 text-xs font-mono uppercase bg-zinc-900 border border-zinc-700 text-zinc-300 cursor-pointer hover:bg-cyan-950 hover:border-cyan-500 hover:text-cyan-400 transition-colors"
                            >
                              {tag}
                            </span>
                          ))}
                       </div>
                       <div className="flex gap-4">
                         <Button variant="primary" onClick={(e) => openChat("User requested demo access.", "Command Center Locked.\n\nGenerating temp access token...\n\nInitiate live stream demo?", e.currentTarget)}>
                           {t('matrix.btn_demo')}
                         </Button>
                       </div>
                    </div>
                 </div>
              </motion.div>
          </div>
        </Section>

        {/* Section 3: Capabilities (Deep Black with Grid) */}
        <Section 
            id="capabilities" 
            title={t('capabilities.title')} 
            subtitle={t('capabilities.subtitle')}
            variant="grid"
            divider="slant-top"
        >
          <motion.div 
            variants={containerVariants}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, margin: "-10% 0px -10% 0px" }}
            className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 relative"
          >
            {/* Visual Circuit Line connecting cards (Desktop) */}
            <div className="absolute top-1/2 left-0 w-full h-[1px] bg-gradient-to-r from-transparent via-white/10 to-transparent -z-10 hidden lg:block" />

            {capabilities.map((item, index) => {
                // Determine Tag color logic based on item theme
                let tagBaseClass = '';
                switch(item.theme) {
                    case 'cyan': tagBaseClass = 'bg-cyan-500/20 text-cyan-200 border-cyan-500/40 hover:bg-cyan-500 hover:text-black hover:shadow-[0_0_15px_#06b6d4]'; break;
                    case 'green': tagBaseClass = 'bg-green-500/20 text-green-200 border-green-500/40 hover:bg-green-500 hover:text-black hover:shadow-[0_0_15px_#22c55e]'; break;
                    case 'pink': tagBaseClass = 'bg-pink-500/20 text-pink-200 border-pink-500/40 hover:bg-pink-500 hover:text-black hover:shadow-[0_0_15px_#ec4899]'; break;
                    case 'red': tagBaseClass = 'bg-red-500/20 text-red-200 border-red-500/40 hover:bg-red-500 hover:text-black hover:shadow-[0_0_15px_#ef4444]'; break;
                    case 'blue': tagBaseClass = 'bg-blue-500/20 text-blue-200 border-blue-500/40 hover:bg-blue-500 hover:text-black hover:shadow-[0_0_15px_#3b82f6]'; break;
                    case 'purple': tagBaseClass = 'bg-purple-500/20 text-purple-200 border-purple-500/40 hover:bg-purple-500 hover:text-black hover:shadow-[0_0_15px_#a855f7]'; break;
                    case 'yellow': tagBaseClass = 'bg-yellow-500/20 text-yellow-200 border-yellow-500/40 hover:bg-yellow-500 hover:text-black hover:shadow-[0_0_15px_#eab308]'; break;
                    case 'orange': tagBaseClass = 'bg-orange-500/20 text-orange-200 border-orange-500/40 hover:bg-orange-500 hover:text-black hover:shadow-[0_0_15px_#f97316]'; break;
                    case 'indigo': tagBaseClass = 'bg-indigo-500/20 text-indigo-200 border-indigo-500/40 hover:bg-indigo-500 hover:text-black hover:shadow-[0_0_15px_#6366f1]'; break;
                    default: tagBaseClass = 'bg-zinc-800 text-zinc-300 border-zinc-600';
                }

                const tags = t(`capabilities.${item.id}_tags`);

                return (
                <motion.div 
                  key={item.id}
                  variants={cardVariants}
                  // Open AI Chat if card itself is clicked (background)
                  onClick={(e) => openChat(`User requested details: ${item.chatContext}`, `Module Selected: ${t(`capabilities.${item.id}_title`).split('. ')[1] || item.chatContext}.\n\nAnalyzing user requirements...\n\nThis module integrates directly with our core AI. Deploying it allows for automated scaling.\n\nInitialize deployment sequence?`, e.currentTarget)}
                  className={`group relative h-full bg-black border ${item.border} ${item.shadow} transition-all duration-500 p-8 flex flex-col cursor-pointer overflow-hidden min-h-[420px] rounded-xl hover:-translate-y-2`}
                >
                   {/* Data Flow Animation - Scanning Line */}
                   <div className={`absolute top-0 left-0 w-full h-[2px] ${item.hoverLine} opacity-0 group-hover:opacity-100 animate-[flow_2s_linear_infinite] shadow-[0_0_10px_currentColor]`} />
                   <div className="absolute inset-0 bg-gradient-to-b from-transparent via-transparent to-black/80 z-0 pointer-events-none"></div>
                   
                   {/* Header Section */}
                   <div className="relative z-10 mb-6 flex justify-between items-start">
                      <div className={`w-14 h-14 bg-zinc-900 border border-white/10 flex items-center justify-center rounded-lg ${item.bg} backdrop-blur-sm transition-all duration-300 group-hover:scale-110 shadow-lg`}>
                         <item.icon className={`w-7 h-7 text-zinc-400 group-hover:${item.color} transition-colors duration-300`} />
                      </div>
                      <div className={`text-xs font-mono font-bold text-zinc-600 group-hover:${item.color} border border-zinc-800 px-2 py-1 rounded bg-black`}>0{index + 1}</div>
                   </div>

                    <h3 className={`relative z-10 text-xl font-bold text-white mb-4 group-hover:${item.color} transition-colors tracking-wide`}>
                        {t(`capabilities.${item.id}_title`)}
                    </h3>
                    
                    <p className="relative z-10 text-zinc-300 text-sm leading-relaxed mb-8 flex-grow font-light border-l-2 border-zinc-800 pl-4 group-hover:border-white/20 transition-colors">
                      {t(`capabilities.${item.id}_desc`)}
                    </p>

                    {/* Interactive Tags */}
                    <div className="relative z-10 flex flex-wrap gap-2 mt-auto">
                       {Array.isArray(tags) && tags.map((tag: string, i: number) => (
                          <button 
                            key={i} 
                            onClick={(e) => {
                                e.stopPropagation(); // Stop card click
                                setActiveFeature({ title: tag, desc: t(`capabilities.${item.id}_desc`), theme: item.theme });
                            }}
                            className={`text-[10px] uppercase font-bold tracking-wider px-3 py-1.5 rounded-sm border transition-all duration-300 ${tagBaseClass}`}
                          >
                            {tag}
                          </button>
                       ))}
                    </div>
                </motion.div>
            )})}

          </motion.div>
        </Section>

         {/* Pricing Section (Light Glass) */}
        <Section 
            id="pricing" 
            title={t('pricing.title')} 
            subtitle={t('pricing.subtitle')} 
            allowOverflow={true}
            variant="glass"
            divider="slant-bottom"
        >
            <PricingSection />
        </Section>

        {/* Section 5: Trust & Partners (Case Studies) - MOVED DOWN */}
        <Section 
            id="trusted-by" 
            title={t('trust.title')} 
            subtitle={t('trust.subtitle')} 
            variant="glass"
            divider="none"
            className="pt-40 pb-24" // Extra padding top to account for slanted overlap from Pricing
        >
          <div ref={trustRef}>
            <div className="mb-24">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 md:gap-8">
                {partners.map((partner, i) => (
                  <motion.div
                    key={partner.name}
                    initial={{ opacity: 0, y: 20 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    viewport={{ once: true }}
                    transition={{ delay: i * 0.1, duration: 0.6 }}
                    className="flex items-center justify-center"
                  >
                    <div 
                      onClick={(e) => openChat(`User queried partner: ${partner.name}`, `Retrieving partner data: ${partner.name}...\n\nStrategic Rating: SSS.\nNode provides foundational compute & data.\n\nView agreement details?`, e.currentTarget)}
                      className="w-full flex items-center justify-center gap-3 px-6 py-6 rounded-none border border-white/5 bg-black/40 hover:border-cyan-500/30 hover:bg-cyan-500/5 transition-all duration-300 cursor-pointer group clip-path-slant"
                    >
                      <partner.icon className="w-5 h-5 text-zinc-500 group-hover:text-cyan-400 transition-colors" />
                      <span className="font-mono font-bold tracking-widest text-zinc-500 group-hover:text-cyan-200 transition-colors">
                        {partner.name}
                      </span>
                    </div>
                  </motion.div>
                ))}
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              {[1, 2, 3].map((item, i) => {
                 const parallaxStyle = i === 1 ? tY2 : (i === 2 ? tY3 : tY1);
                 const author = t(`trust.t${item}_author`);
                 const company = t(`trust.t${item}_company`);
                 return (
                  <motion.div
                    key={i}
                    style={{ y: parallaxStyle }}
                    className="relative group h-full cursor-pointer"
                    onClick={(e) => openChat(`User asked about case study: ${company}`, `Case Study Analysis: ${company}\n\nOutcome: 300% Efficiency Increase.\nDeployed: Auto-Scaling Neural Agents.\n\nWould you like to see the exact configuration used?`, e.currentTarget)}
                  >
                    <div className="absolute -inset-0.5 bg-gradient-to-b from-cyan-500/20 to-purple-500/20 opacity-0 group-hover:opacity-100 transition-opacity duration-500 blur-md"></div>
                    <div className="relative h-full bg-zinc-950 p-8 border-l-2 border-white/10 group-hover:border-cyan-500 transition-all duration-300 flex flex-col">
                      <div className="flex justify-between items-start mb-6">
                        <Quote className="w-8 h-8 text-zinc-800 group-hover:text-cyan-500/20 transition-colors" />
                        <div className="opacity-0 group-hover:opacity-100 transition-opacity text-[10px] text-cyan-500 font-mono border border-cyan-500/30 px-2 py-1 rounded">CASE_ID_{100 + i}</div>
                      </div>
                      
                      <div className="mb-8 flex-grow">
                        <p className="text-zinc-300 leading-relaxed font-light text-lg">
                          "{t(`trust.t${item}_text`)}"
                        </p>
                      </div>
                      
                      <div className="pt-6 border-t border-white/5">
                        <div className="flex items-center gap-3">
                          <div className="w-10 h-10 bg-zinc-900 border border-white/10 flex items-center justify-center group-hover:border-cyan-500/30 transition-colors">
                             <span className="font-mono text-sm text-cyan-500 font-bold">{author.charAt(0)}</span>
                          </div>
                          <div>
                            <div className="text-sm font-bold text-white font-mono">{author.split(' // ')[0]}</div>
                            <div className="text-xs uppercase tracking-wider text-zinc-500 group-hover:text-cyan-400 transition-colors">
                              {company}
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </motion.div>
                );
              })}
            </div>
          </div>
        </Section>

        {/* Footer */}
        <footer className="relative py-20 border-t border-zinc-800 bg-black overflow-hidden z-10" id="contact">
            {/* Background Grid */}
            <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.02)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.02)_1px,transparent_1px)] bg-[size:40px_40px] pointer-events-none"></div>

            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
                <div className="flex flex-col lg:flex-row justify-between items-end gap-12">
                    
                    {/* Brand & CTA */}
                    <div className="flex flex-col items-center lg:items-start gap-8 w-full lg:w-auto">
                        <div className="text-center lg:text-left">
                             <span className="font-mono text-3xl font-bold tracking-widest text-white block mb-2">
                              SMART_CONTROL<span className="text-cyan-500">_</span>KING
                            </span>
                            <p className="text-zinc-500 text-sm max-w-md font-mono">
                              {t('nav.tagline')}
                            </p>
                        </div>
                        
                         <button 
                            onClick={() => setShowContactModal(true)}
                            data-robot-avoid="true"
                            className="group relative px-8 py-4 font-mono text-sm font-bold tracking-wider uppercase bg-zinc-900 text-cyan-400 border border-cyan-500/30 overflow-hidden transition-all hover:border-cyan-400 hover:text-cyan-200 hover:shadow-[0_0_20px_rgba(0,255,255,0.4)] w-full lg:w-auto clip-path-slant"
                          >
                            <div className="absolute inset-0 w-full h-full bg-cyan-500/10 translate-y-full group-hover:translate-y-0 transition-transform duration-300 ease-out"></div>
                            <span className="relative flex items-center justify-center gap-2">
                              <Calendar className="w-4 h-4" />
                              {t('nav.schedule')}
                            </span>
                         </button>
                         
                         {/* AI Receptionist Link */}
                         <div 
                            className="flex items-center gap-2 text-[10px] text-zinc-500 font-mono cursor-pointer hover:text-cyan-400 transition-colors"
                            onClick={(e) => openChat('User seeking support from footer.', 'Receptionist AI Online.\n\nI can assist you with:\n- Booking a demo\n- Technical support\n- Partnership inquiries\n\nHow can I direct you?', e.currentTarget)}
                         >
                            <span className="w-1.5 h-1.5 bg-green-500 rounded-full animate-pulse"></span>
                            AI Receptionist Standing By
                         </div>
                    </div>

                    {/* Social Matrix */}
                    <div className="flex flex-wrap justify-center gap-4 robot-avoid-zone">
                        {/* Telegram */}
                        <a href={config.contact.telegram} target="_blank" rel="noopener noreferrer" data-robot-avoid="true" className="group flex flex-col items-center justify-center w-20 h-20 bg-zinc-900 border border-zinc-800 hover:border-[#229ED9] hover:bg-[#229ED9]/10 transition-all duration-300">
                            <TelegramIcon className="w-6 h-6 text-zinc-500 group-hover:text-[#229ED9] mb-2 transition-colors" />
                            <span className="text-[9px] font-mono text-zinc-600 group-hover:text-[#229ED9]">TG</span>
                        </a>

                        {/* Gmail */}
                        <a href={`mailto:${config.contact.email}`} data-robot-avoid="true" className="group flex flex-col items-center justify-center w-20 h-20 bg-zinc-900 border border-zinc-800 hover:border-[#EA4335] hover:bg-[#EA4335]/10 transition-all duration-300">
                            <GmailIcon className="w-6 h-6 text-zinc-500 group-hover:text-[#EA4335] mb-2 transition-colors" />
                            <span className="text-[9px] font-mono text-zinc-600 group-hover:text-[#EA4335]">MAIL</span>
                        </a>

                        {/* WhatsApp (原 LinkedIn 位置) */}
                        <a href={config.contact.whatsapp} target="_blank" rel="noopener noreferrer" data-robot-avoid="true" className="group flex flex-col items-center justify-center w-20 h-20 bg-zinc-900 border border-zinc-800 hover:border-[#25D366] hover:bg-[#25D366]/10 transition-all duration-300">
                            <WhatsAppIcon className="w-6 h-6 text-zinc-500 group-hover:text-[#25D366] mb-2 transition-colors" />
                            <span className="text-[9px] font-mono text-zinc-600 group-hover:text-[#25D366]">WA</span>
                        </a>

                        {/* Twitter/X */}
                        <a href={config.contact.twitter} target="_blank" rel="noopener noreferrer" data-robot-avoid="true" className="group flex flex-col items-center justify-center w-20 h-20 bg-zinc-900 border border-zinc-800 hover:border-white hover:bg-white/5 transition-all duration-300">
                            <Twitter className="w-6 h-6 text-zinc-500 group-hover:text-white mb-2 transition-colors" />
                            <span className="text-[9px] font-mono text-zinc-600 group-hover:text-white">X</span>
                        </a>
                    </div>

                    {/* System Status */}
                    <div className="text-center lg:text-right w-full lg:w-auto">
                        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-zinc-900 border border-zinc-800 mb-4">
                            <span className="w-2 h-2 rounded-full bg-cyan-500 animate-pulse"></span>
                            <span className="text-[10px] font-mono text-zinc-400">{t('nav.system_stable')}</span>
                        </div>
                         <div className="text-zinc-600 text-xs font-mono">
                          <Link to="/system/8492-AX" className="hover:text-cyan-400 transition-colors cursor-pointer block mb-1">
                            ID: 8492-AX
                          </Link> 
                          {t('nav.rights')}
                       </div>
                    </div>

                </div>
            </div>
        </footer>

      </main>
    </div>
  );
};

const App: React.FC = () => {
  return (
    <AIChatProvider>
      <HashRouter>
        <Routes>
          <Route path="/" element={<LandingContent />} />
          <Route path="/system/:id" element={<SystemDetails />} />
        </Routes>
      </HashRouter>
    </AIChatProvider>
  );
};

export default App;
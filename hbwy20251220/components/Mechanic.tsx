import React from 'react';
import { motion } from 'framer-motion';
import { Gift, Rocket, UserPlus } from 'lucide-react';

const StepCard = ({ icon: Icon, title, sub, desc, delay, accentColor }: any) => (
  <motion.div 
    initial={{ opacity: 0, y: 60 }}
    whileInView={{ opacity: 1, y: 0 }}
    viewport={{ once: true, amount: 0.2 }}
    transition={{ duration: 0.6, delay, ease: "easeOut" }}
    className="relative flex-1 bg-game-card border border-white/5 p-8 rounded-3xl group hover:bg-game-surface transition-colors duration-300"
  >
    <div className={`w-14 h-14 rounded-2xl flex items-center justify-center mb-6 bg-gradient-to-br ${accentColor} shadow-lg group-hover:scale-110 transition-transform duration-300`}>
      <Icon className="w-7 h-7 text-white" />
    </div>
    <h3 className="text-xl font-display font-bold mb-2 group-hover:text-white transition-colors">{title}</h3>
    <p className="text-xs font-bold text-gray-500 uppercase tracking-wider mb-4">{sub}</p>
    <p className="text-game-text text-sm leading-relaxed">{desc}</p>
    
    {/* Decorative corner glow */}
    <div className={`absolute top-0 right-0 w-20 h-20 bg-gradient-to-br ${accentColor} opacity-0 group-hover:opacity-10 blur-xl rounded-full transition-opacity duration-500 pointer-events-none`} />
  </motion.div>
);

export const Mechanic = () => {
  return (
    <section id="mechanic" className="py-24 relative overflow-hidden">
      <div className="max-w-7xl mx-auto px-6">
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="text-center mb-20"
        >
          <h2 className="text-3xl md:text-5xl font-display font-bold mb-4">
            最简单粗暴的增长引擎
          </h2>
          <p className="text-gray-400">The Viral Loop - 基于人性贪婪的闭环设计</p>
        </motion.div>

        <div className="flex flex-col md:flex-row gap-8 relative">
          {/* Connecting Line */}
          <div className="hidden md:block absolute top-1/2 left-0 w-full h-[2px] bg-gradient-to-r from-transparent via-white/10 to-transparent -translate-y-8 z-0"></div>

          <StepCard 
            icon={Gift} 
            title="瞬间刺激" 
            sub="Instant Gratification"
            desc="用户点击 Mini App，直接开抢 USDT/TON 或积分。真金白银，秒到账，刺激感拉满。"
            delay={0.2}
            accentColor="from-orange-500 to-red-500"
          />
          
          <StepCard 
            icon={UserPlus} 
            title="社交续命" 
            sub="Social Recharge"
            desc="机会用完？必须邀请 N 个好友、加入频道或完成任务才能获得新的“钥匙”继续抢。"
            delay={0.4}
            accentColor="from-purple-500 to-indigo-500"
          />

          <StepCard 
            icon={Rocket} 
            title="指数增长" 
            sub="Exponential Growth"
            desc="被邀请者为了抢红包，重复上述过程。您的用户基数开始呈指数级爆炸。"
            delay={0.6}
            accentColor="from-green-500 to-emerald-600"
          />
        </div>
      </div>
    </section>
  );
};
import React from 'react';
import { DollarSign, Ticket, TrendingUp } from 'lucide-react';

const RevenueCard = ({ icon: Icon, title, desc }: any) => (
  <div className="p-8 bg-game-card border border-white/5 hover:border-game-primary/50 rounded-3xl text-center transition-all group hover:-translate-y-1 hover:shadow-2xl hover:shadow-orange-500/10">
    <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-white/5 mb-6 group-hover:bg-game-primary group-hover:text-white text-gray-400 transition-all">
      <Icon className="w-8 h-8" />
    </div>
    <h3 className="text-xl font-bold mb-3 font-display">{title}</h3>
    <p className="text-gray-400 text-sm leading-relaxed">{desc}</p>
  </div>
);

export const Revenue = () => {
  return (
    <section className="py-24 bg-game-dark border-t border-white/5">
      <div className="max-w-5xl mx-auto px-6 text-center">
        <h2 className="text-3xl md:text-5xl font-display font-bold mb-16">
          不仅仅是赚吆喝，<br/>更是<span className="text-transparent bg-clip-text bg-gradient-to-r from-orange-400 to-red-500">赚利润</span>
        </h2>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <RevenueCard 
            icon={DollarSign}
            title="流水抽成 (Rake)"
            desc="在扫雷等博弈模式中，平台自动抽取每局获胜者 1%-5% 的手续费。"
          />
          <RevenueCard 
            icon={Ticket}
            title="门票机制 (Entry)"
            desc="用户需要支付少量 TON 或积分购买“入场券”才能参与高级红包场。"
          />
          <RevenueCard 
            icon={TrendingUp}
            title="流量变现 (Ads)"
            desc="将巨大的参与流量引导至您的其他高利润项目（如交易所注册、代币预售）。"
          />
        </div>
      </div>
    </section>
  );
};
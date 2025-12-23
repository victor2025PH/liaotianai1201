import React from 'react';
import { Check } from 'lucide-react';
import { motion } from 'framer-motion';

const Pricing: React.FC = () => {
  return (
    <section id="pricing" className="py-24 bg-dark-bg">
      <div className="container mx-auto px-4">
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-4xl font-bold mb-4">套餐报价</h2>
          <p className="text-gray-400">透明定价，拒绝隐形消费</p>
        </div>

        <div className="grid lg:grid-cols-3 gap-8 max-w-6xl mx-auto items-center">
          
          {/* MVP */}
          <div className="bg-dark-card border border-dark-border p-8 rounded-2xl">
            <h3 className="text-xl font-bold text-gray-300">MVP 极速版</h3>
            <p className="text-sm text-gray-500 mt-2">验证想法、简单的引流工具</p>
            <div className="my-6">
              <span className="text-3xl font-bold text-white">1,500 USDT</span>
              <span className="text-gray-500 text-sm"> 起</span>
            </div>
            <ul className="space-y-4 mb-8">
              {['3-5 天交付', '基础 UI 设计', '用户一键登录', '基础展示页面'].map((item, i) => (
                <li key={i} className="flex items-center gap-2 text-sm text-gray-400">
                  <Check className="w-4 h-4 text-gray-500" /> {item}
                </li>
              ))}
            </ul>
            <button className="w-full py-3 border border-dark-border rounded-lg text-gray-300 hover:bg-white/5 transition-colors">
              选择 MVP
            </button>
          </div>

          {/* Business - Highlighted */}
          <motion.div 
            whileHover={{ y: -5 }}
            className="bg-[#0f0f0f] border-2 border-neon-blue p-8 rounded-2xl relative shadow-[0_0_30px_rgba(0,243,255,0.1)] transform scale-105 z-10"
          >
            <div className="absolute top-0 right-0 bg-neon-blue text-black text-xs font-bold px-3 py-1 rounded-bl-lg rounded-tr-lg">
              BEST VALUE
            </div>
            <h3 className="text-2xl font-bold text-white">商业运营版</h3>
            <p className="text-sm text-gray-400 mt-2">电商、付费订阅、复杂工具</p>
            <div className="my-6">
              <span className="text-4xl font-bold text-neon-blue">3,500 USDT</span>
              <span className="text-gray-500 text-sm"> 起</span>
            </div>
            <ul className="space-y-4 mb-8">
              {['7-14 天交付', '完整支付接口 (Crypto/Fiat)', '管理后台 (Admin Panel)', '邀请裂变系统', '专业 UI/UX 设计'].map((item, i) => (
                <li key={i} className="flex items-center gap-2 text-sm text-white">
                  <Check className="w-4 h-4 text-neon-blue" /> {item}
                </li>
              ))}
            </ul>
            <button className="w-full py-3 bg-neon-blue text-black font-bold rounded-lg hover:bg-cyan-400 transition-colors shadow-lg shadow-neon-blue/20">
              立即咨询方案
            </button>
          </motion.div>

          {/* GameFi */}
          <div className="bg-dark-card border border-dark-border p-8 rounded-2xl">
            <h3 className="text-xl font-bold text-gray-300">游戏化定制版</h3>
            <p className="text-sm text-gray-500 mt-2">复刻 Notcoin/Catizen 级项目</p>
            <div className="my-6">
              <span className="text-3xl font-bold text-white">8,000 USDT</span>
              <span className="text-gray-500 text-sm"> 起</span>
            </div>
            <ul className="space-y-4 mb-8">
              {['20 天+ 交付周期', '复杂游戏逻辑开发', '高并发性能优化', '反作弊风控系统', 'Web3 钱包深度集成'].map((item, i) => (
                <li key={i} className="flex items-center gap-2 text-sm text-gray-400">
                  <Check className="w-4 h-4 text-neon-purple" /> {item}
                </li>
              ))}
            </ul>
            <button className="w-full py-3 border border-dark-border rounded-lg text-gray-300 hover:bg-white/5 transition-colors">
              定制开发
            </button>
          </div>

        </div>
      </div>
    </section>
  );
};

export default Pricing;
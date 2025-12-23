import React from 'react';
import { motion } from 'framer-motion';
import { Coins, Bomb, Lock } from 'lucide-react';

const ModeCard = ({ title, type, desc, purpose, fit, icon: Icon, gradient }: any) => (
  <motion.div 
    whileHover={{ y: -5 }}
    className="bg-game-card border border-white/5 p-1 rounded-3xl relative overflow-hidden group"
  >
    {/* Inner Card Content */}
    <div className="bg-game-card rounded-[22px] p-7 h-full relative z-10">
        <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${gradient} flex items-center justify-center mb-6`}>
            <Icon className="text-white w-6 h-6" />
        </div>
        
        <h3 className="text-2xl font-display font-bold text-white mb-4 group-hover:text-transparent group-hover:bg-clip-text group-hover:bg-gradient-to-r group-hover:from-white group-hover:to-gray-400 transition-all">{title}</h3>
        
        <div className="space-y-4">
            <div>
            <span className="text-xs font-bold text-gray-500 uppercase tracking-wider block mb-1">玩法</span>
            <p className="text-gray-300 text-sm">{type}</p>
            </div>
            <div>
            <span className="text-xs font-bold text-gray-500 uppercase tracking-wider block mb-1">目的</span>
            <p className="text-gray-300 text-sm">{purpose}</p>
            </div>
            <div className="pt-4 border-t border-white/5">
            <div className="px-3 py-1 bg-white/5 rounded-lg inline-block">
                <p className="text-gray-400 text-xs font-medium">{fit}</p>
            </div>
            </div>
        </div>
    </div>
    
    {/* Gradient Glow Effect on Hover */}
    <div className={`absolute inset-0 bg-gradient-to-br ${gradient} opacity-0 group-hover:opacity-10 transition-opacity duration-500`}></div>
  </motion.div>
);

export const GameModes = () => {
  return (
    <section id="modes" className="py-24 bg-game-dark">
      <div className="max-w-7xl mx-auto px-6">
        <div className="mb-16 flex flex-col md:flex-row md:items-end justify-between gap-4">
          <div>
            <h2 className="text-3xl md:text-4xl font-display font-bold mb-4">
               多种 Web3 玩法模型
            </h2>
            <p className="text-gray-400 max-w-2xl">
                经过市场验证的高转化模型，支持 <span className="text-white">USDT</span>, <span className="text-white">TON</span> 或 <span className="text-white">自定义代币</span>。
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <ModeCard 
            title="经典红包雨"
            icon={Coins}
            gradient="from-yellow-400 to-orange-500"
            type="定时开启，拼手气抢份额，先到先得。"
            purpose="短时间内聚集超高人气，为频道/群组瞬间增粉。"
            fit="项目冷启动、节日营销"
          />
          
          <ModeCard 
            title="扫雷博弈"
            icon={Bomb}
            gradient="from-red-500 to-pink-600"
            type="设置“雷号”（如尾数7），抢到雷者赔付多倍金额。"
            purpose="高频互动，资金快速流转，平台抽取流水手续费。"
            fit="活跃社群、GameFi"
          />

          <ModeCard 
            title="任务解锁"
            icon={Lock}
            gradient="from-blue-500 to-purple-600"
            type="必须完成特定 Web3 任务（连钱包、持NFT）才能开红包。"
            purpose="精准筛选高价值 Web3 用户，进行空投引导。"
            fit="空投预热、白名单"
          />
        </div>
      </div>
    </section>
  );
};
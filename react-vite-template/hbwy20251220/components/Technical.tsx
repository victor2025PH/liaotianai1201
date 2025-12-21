import React from 'react';
import { Shield, Zap, Eye, Bot, Lock } from 'lucide-react';

const TechItem = ({ icon: Icon, title, desc }: any) => (
  <div className="flex items-start gap-5 p-4 rounded-2xl hover:bg-white/5 transition-colors">
    <div className="p-3 bg-game-surface rounded-xl border border-white/5 shrink-0 shadow-sm">
      <Icon className="w-6 h-6 text-game-primary" />
    </div>
    <div>
      <h3 className="text-lg font-bold text-white mb-2">{title}</h3>
      <p className="text-gray-400 text-sm leading-relaxed">{desc}</p>
    </div>
  </div>
);

export const Technical = () => {
  return (
    <section id="tech" className="py-24 relative bg-game-dark">
      <div className="max-w-7xl mx-auto px-6 grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
        
        {/* Left Side: Content */}
        <div>
          <div className="inline-flex items-center gap-2 px-3 py-1 bg-purple-500/10 rounded-full border border-purple-500/20 mb-6">
            <Lock size={14} className="text-purple-400" />
            <span className="text-xs font-bold uppercase tracking-wider text-purple-300">Enterprise Grade Security</span>
          </div>
          
          <h2 className="text-3xl md:text-5xl font-display font-bold mb-8">
            Technical Muscle<br/>
            <span className="text-gray-600">安全与稳定就是一切</span>
          </h2>

          <div className="space-y-4">
            <TechItem 
              icon={Shield}
              title="资金安全锁 (Crypto Escrow)"
              desc="拒绝中心化资金池风险。可选基于 TON 智能合约的多签托管，红包金额链上锁定，用户抢到直接触发合约转账，公开透明。"
            />
            <TechItem 
              icon={Zap}
              title="高并发底座 (High Concurrency)"
              desc="基于 Go/Python (FastAPI) + Redis 集群的极速后端。经受过单秒 50,000+ QPS 的抢红包压力测试，丝般顺滑。"
            />
            <TechItem 
              icon={Eye}
              title="毫秒级反作弊 (Anti-Cheat)"
              desc="核心设备指纹与 IP 风险库。秒杀脚本怪、模拟器集群和批量注册的羊毛党，确保红包发给真实用户。"
            />
            <TechItem 
              icon={Bot}
              title="Bot 深度联动"
              desc="游戏结果实时推送到群组，营造紧张刺激的氛围，激发群成员参与欲。"
            />
          </div>
        </div>

        {/* Right Side: Visual */}
        <div className="relative">
          <div className="absolute inset-0 bg-gradient-to-r from-orange-500/20 to-purple-600/20 blur-[100px] rounded-full z-0" />
          <div className="relative z-10 bg-game-card border border-white/10 rounded-3xl p-8 shadow-2xl">
             {/* Mock Code Block */}
             <div className="flex items-center gap-2 mb-6 border-b border-white/5 pb-4">
                <div className="w-3 h-3 rounded-full bg-red-500"></div>
                <div className="w-3 h-3 rounded-full bg-yellow-500"></div>
                <div className="w-3 h-3 rounded-full bg-green-500"></div>
                <span className="ml-2 text-xs text-gray-500 font-mono">contract_audit.sol</span>
             </div>
             <div className="font-mono text-xs md:text-sm text-gray-400 space-y-3">
               <p><span className="text-purple-400">function</span> <span className="text-blue-400">claimRedEnvelope</span>(uint256 id) <span className="text-purple-400">external</span> <span className="text-purple-400">nonReentrant</span> {'{'}</p>
               <p className="pl-4 text-gray-500">// Verify Merkle Proof & Anti-Cheat</p>
               <p className="pl-4">require(<span className="text-yellow-400">{'!isBot(msg.sender)'}</span>, "Bot detected");</p>
               <p className="pl-4">require(<span className="text-yellow-400">{'remainingAmount > 0'}</span>, "Empty");</p>
               <p className="pl-4 text-gray-500">// Atomic Transfer via TON/USDT</p>
               <p className="pl-4"><span className="text-blue-400">IERC20</span>(token).transfer(msg.sender, amount);</p>
               <p className="pl-4"><span className="text-blue-400">emit</span> <span className="text-blue-400">Claimed</span>(msg.sender, amount);</p>
               <p>{'}'}</p>
               <p className="mt-6 text-green-500 font-bold bg-green-500/10 p-2 rounded border border-green-500/20 inline-block">// {'>'} AUDIT PASSED: 0 Critical Vulnerabilities</p>
             </div>
          </div>
          
          {/* Floating Badge */}
          <div className="absolute -bottom-6 -right-6 bg-game-card border border-white/10 p-4 rounded-2xl shadow-xl flex items-center gap-4 animate-float">
             <div className="relative">
                <div className="w-3 h-3 rounded-full bg-green-500 relative z-10"></div>
                <div className="absolute inset-0 bg-green-500 rounded-full animate-ping"></div>
             </div>
             <div>
                <p className="text-xs text-gray-400 uppercase font-bold tracking-wider">Status</p>
                <p className="font-bold text-white">100% Uptime</p>
             </div>
          </div>
        </div>

      </div>
    </section>
  );
};
import React from 'react';
import { motion } from 'framer-motion';
import { Gamepad2, ShoppingBag, Users } from 'lucide-react';

const UseCases: React.FC = () => {
  return (
    <section id="use-cases" className="py-20 bg-dark-bg">
      <div className="container mx-auto px-4">
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-4xl font-bold">热门落地场景</h2>
        </div>

        <div className="grid lg:grid-cols-3 gap-8">
          
          {/* GameFi */}
          <motion.div 
            whileHover={{ y: -10 }}
            className="group relative p-[1px] rounded-2xl bg-gradient-to-b from-neon-purple/50 to-transparent"
          >
            <div className="bg-dark-card h-full rounded-2xl p-8 relative overflow-hidden">
              <div className="absolute -right-6 -top-6 bg-neon-purple/10 w-32 h-32 rounded-full blur-2xl group-hover:bg-neon-purple/20 transition-all"></div>
              
              <Gamepad2 className="w-12 h-12 text-neon-purple mb-6" />
              <h3 className="text-xl font-bold mb-2">GameFi & 互动娱乐</h3>
              <div className="w-10 h-1 bg-neon-purple mb-4"></div>
              
              <p className="text-gray-400 text-sm mb-4">
                Tap-to-Earn、红包扫雷、养成类游戏。
              </p>
              <div className="space-y-2 border-t border-white/10 pt-4">
                <p className="text-xs text-gray-500 font-mono">
                  <span className="text-white font-bold">功能：</span> 每日签到、能量恢复、好友组队
                </p>
                <p className="text-xs text-gray-500 font-mono">
                  <span className="text-white font-bold">价值：</span> 低获客成本，高粘性
                </p>
              </div>
            </div>
          </motion.div>

          {/* E-commerce */}
          <motion.div 
            whileHover={{ y: -10 }}
            className="group relative p-[1px] rounded-2xl bg-gradient-to-b from-neon-blue/50 to-transparent"
          >
            <div className="bg-dark-card h-full rounded-2xl p-8 relative overflow-hidden">
              <div className="absolute -right-6 -top-6 bg-neon-blue/10 w-32 h-32 rounded-full blur-2xl group-hover:bg-neon-blue/20 transition-all"></div>
              
              <ShoppingBag className="w-12 h-12 text-neon-blue mb-6" />
              <h3 className="text-xl font-bold mb-2">电商与虚拟资产</h3>
              <div className="w-10 h-1 bg-neon-blue mb-4"></div>
              
              <p className="text-gray-400 text-sm mb-4">
                礼品卡售卖、虚拟账号发货、独立站。
              </p>
              <div className="space-y-2 border-t border-white/10 pt-4">
                <p className="text-xs text-gray-500 font-mono">
                  <span className="text-white font-bold">功能：</span> 购物车、订单追踪、自动发货
                </p>
                <p className="text-xs text-gray-500 font-mono">
                  <span className="text-white font-bold">价值：</span> 缩短决策链路，即时成交
                </p>
              </div>
            </div>
          </motion.div>

          {/* Subscription */}
          <motion.div 
            whileHover={{ y: -10 }}
            className="group relative p-[1px] rounded-2xl bg-gradient-to-b from-neon-pink/50 to-transparent"
          >
            <div className="bg-dark-card h-full rounded-2xl p-8 relative overflow-hidden">
              <div className="absolute -right-6 -top-6 bg-neon-pink/10 w-32 h-32 rounded-full blur-2xl group-hover:bg-neon-pink/20 transition-all"></div>
              
              <Users className="w-12 h-12 text-neon-pink mb-6" />
              <h3 className="text-xl font-bold mb-2">会员订阅 & 社群</h3>
              <div className="w-10 h-1 bg-neon-pink mb-4"></div>
              
              <p className="text-gray-400 text-sm mb-4">
                知识付费、VIP 信号群、私密圈子。
              </p>
              <div className="space-y-2 border-t border-white/10 pt-4">
                <p className="text-xs text-gray-500 font-mono">
                  <span className="text-white font-bold">功能：</span> 付费解锁、过期踢人、分销
                </p>
                <p className="text-xs text-gray-500 font-mono">
                  <span className="text-white font-bold">价值：</span> 私域自动化，被动收入
                </p>
              </div>
            </div>
          </motion.div>

        </div>
      </div>
    </section>
  );
};

export default UseCases;
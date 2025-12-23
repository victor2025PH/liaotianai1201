import React from 'react';
import { motion } from 'framer-motion';
import { XCircle, CheckCircle, Smartphone, CreditCard, TrendingUp } from 'lucide-react';

const PainPoints: React.FC = () => {
  return (
    <section id="pain-points" className="py-20 bg-dark-bg relative">
      <div className="container mx-auto px-4">
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-4xl font-bold mb-4">
            传统 APP 已死，<span className="text-neon-blue">Mini App 当立</span>
          </h2>
          <p className="text-gray-400">Why Build on Telegram?</p>
        </div>

        <div className="grid md:grid-cols-2 gap-8 lg:gap-12 max-w-5xl mx-auto">
          
          {/* Traditional App - Pain */}
          <motion.div 
            initial={{ opacity: 0, x: -50 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            className="bg-[#1a1a1a]/50 border border-red-900/30 rounded-2xl p-8 backdrop-blur-sm relative overflow-hidden group"
          >
            <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-red-600 to-transparent"></div>
            <h3 className="text-2xl font-bold mb-6 flex items-center gap-3 text-red-500">
              <XCircle /> 传统困局
            </h3>
            
            <div className="space-y-6">
              <div className="flex gap-4">
                <div className="mt-1 bg-red-900/20 p-2 rounded h-fit">
                  <Smartphone className="w-5 h-5 text-red-500" />
                </div>
                <div>
                  <h4 className="font-bold text-gray-200">下载门槛高</h4>
                  <p className="text-gray-500 text-sm mt-1">用户听到“下载APP”就流失 50%。</p>
                </div>
              </div>

              <div className="flex gap-4">
                <div className="mt-1 bg-red-900/20 p-2 rounded h-fit">
                  <CreditCard className="w-5 h-5 text-red-500" />
                </div>
                <div>
                  <h4 className="font-bold text-gray-200">支付繁琐</h4>
                  <p className="text-gray-500 text-sm mt-1">跳出应用支付，转化率极低，信任成本高。</p>
                </div>
              </div>

              <div className="flex gap-4">
                <div className="mt-1 bg-red-900/20 p-2 rounded h-fit">
                  <TrendingUp className="w-5 h-5 text-red-500" />
                </div>
                <div>
                  <h4 className="font-bold text-gray-200">推广昂贵</h4>
                  <p className="text-gray-500 text-sm mt-1">买量成本 $10+/人，难以回本，ROI 惨不忍睹。</p>
                </div>
              </div>
            </div>
          </motion.div>

          {/* TMA - Solution */}
          <motion.div 
            initial={{ opacity: 0, x: 50 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            className="bg-[#1a1a1a]/80 border border-green-900/30 rounded-2xl p-8 backdrop-blur-sm relative overflow-hidden ring-1 ring-green-500/20"
          >
            <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-neon-green to-transparent"></div>
            <div className="absolute inset-0 bg-neon-green/5 animate-pulse pointer-events-none"></div>
            <h3 className="text-2xl font-bold mb-6 flex items-center gap-3 text-neon-green">
              <CheckCircle /> TMA 破局
            </h3>
            
            <div className="space-y-6 relative z-10">
              <div className="flex gap-4">
                <div className="mt-1 bg-green-900/20 p-2 rounded h-fit">
                  <Smartphone className="w-5 h-5 text-neon-green" />
                </div>
                <div>
                  <h4 className="font-bold text-white">即点即用</h4>
                  <p className="text-gray-400 text-sm mt-1">嵌入聊天窗口，0 秒启动，转化率提升 5 倍。</p>
                </div>
              </div>

              <div className="flex gap-4">
                <div className="mt-1 bg-green-900/20 p-2 rounded h-fit">
                  <CreditCard className="w-5 h-5 text-neon-green" />
                </div>
                <div>
                  <h4 className="font-bold text-white">原生支付</h4>
                  <p className="text-gray-400 text-sm mt-1">支持 USDT/TON/法币直接支付，极速到账。</p>
                </div>
              </div>

              <div className="flex gap-4">
                <div className="mt-1 bg-green-900/20 p-2 rounded h-fit">
                  <TrendingUp className="w-5 h-5 text-neon-green" />
                </div>
                <div>
                  <h4 className="font-bold text-white">社交裂变</h4>
                  <p className="text-gray-400 text-sm mt-1">利用 Telegram 强大的转发机制，低成本获取指数级增长。</p>
                </div>
              </div>
            </div>
          </motion.div>

        </div>
      </div>
    </section>
  );
};

export default PainPoints;
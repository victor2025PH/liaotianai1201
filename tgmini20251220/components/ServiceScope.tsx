import React from 'react';
import { motion } from 'framer-motion';
import { Layout, Server, Wallet, Share2 } from 'lucide-react';

const services = [
  {
    icon: Layout,
    title: "交互层：原生级 UI/UX 设计",
    color: "text-blue-400",
    features: [
      "沉浸式体验：适配 Telegram Dark Mode",
      "流畅丝滑的 60fps 动画体验",
      "组件：TWA 滑动弹窗, 震动反馈"
    ]
  },
  {
    icon: Server,
    title: "逻辑层：高性能后端",
    color: "text-purple-400",
    features: [
      "FastAPI 微服务，万人高并发",
      "Telegram ID 一键免密登录",
      "严密的 initData 校验防止作弊"
    ]
  },
  {
    icon: Wallet,
    title: "变现层：多维支付聚合",
    color: "text-green-400",
    features: [
      "Telegram Stars 官方支付接入",
      "TON Connect (USDT/TON/NFT)",
      "Stripe/PayPal 法币收款支持"
    ]
  },
  {
    icon: Share2,
    title: "裂变层：病毒营销引擎",
    color: "text-pink-400",
    features: [
      "Invite-to-Earn 邀请追踪系统",
      "实时排行榜（日榜/周榜）",
      "Airdrop Task 频道导流任务"
    ]
  }
];

const ServiceScope: React.FC = () => {
  return (
    <section id="services" className="py-20 bg-black relative">
      <div className="absolute top-0 right-0 w-1/3 h-full bg-gradient-to-l from-blue-900/10 to-transparent pointer-events-none"></div>
      
      <div className="container mx-auto px-4 relative z-10">
        <div className="mb-16">
          <h2 className="text-3xl md:text-4xl font-bold mb-4">全案服务内容</h2>
          <p className="text-gray-400 max-w-2xl">我们不仅仅写代码，我们构建商业闭环。</p>
        </div>

        <div className="grid md:grid-cols-2 gap-6">
          {services.map((service, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: index * 0.1 }}
              className="bg-dark-card border border-dark-border p-8 rounded-xl hover:border-neon-blue/50 hover:bg-dark-card/80 transition-all group"
            >
              <div className="flex items-start gap-4">
                <div className={`p-3 bg-white/5 rounded-lg ${service.color}`}>
                  <service.icon className="w-8 h-8" />
                </div>
                <div>
                  <h3 className="text-xl font-bold text-white mb-2 font-mono">
                    <span className="opacity-50 text-sm mr-2">0{index + 1}.</span>
                    {service.title.split('：')[1]}
                  </h3>
                  <ul className="space-y-2 mt-4">
                    {service.features.map((feature, fIndex) => (
                      <li key={fIndex} className="text-gray-400 text-sm flex items-center gap-2">
                        <span className={`w-1.5 h-1.5 rounded-full ${service.color.replace('text-', 'bg-')}`}></span>
                        {feature}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
};

export default ServiceScope;
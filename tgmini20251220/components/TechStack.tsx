import React from 'react';
import { motion } from 'framer-motion';

const techs = [
  { name: 'React 18', cat: '前端开发', desc: '极致响应速度' },
  { name: 'Framer Motion', cat: '交互动画', desc: '炫酷动画' },
  { name: 'Python FastAPI', cat: '后端架构', desc: '微服务架构' },
  { name: 'PostgreSQL', cat: '数据存储', desc: '可靠数据存储' },
  { name: 'TON SDK', cat: '区块链', desc: '原生链上交互' },
  { name: 'FunC / Tact', cat: '智能合约', desc: 'Web3 必备' },
  { name: 'Docker / K8s', cat: '运维部署', desc: '自动化部署' },
  { name: 'Redis', cat: '高速缓存', desc: '高并发缓存' },
];

const TechStack: React.FC = () => {
  return (
    <section id="tech" className="py-20 bg-black/50 border-y border-dark-border overflow-hidden">
      <div className="container mx-auto px-4">
        <div className="flex flex-col md:flex-row items-center justify-between mb-12">
          <h2 className="text-3xl font-bold font-mono">
            <span className="text-neon-blue">&lt;</span>
            核心技术引擎
            <span className="text-neon-blue">/&gt;</span>
          </h2>
          <span className="text-sm text-gray-500 font-mono mt-2 md:mt-0">领域核心技术优势</span>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {techs.map((tech, index) => (
            <motion.div
              key={index}
              whileHover={{ scale: 1.02, backgroundColor: "rgba(255,255,255,0.03)" }}
              className="border border-dark-border p-6 rounded bg-dark-card/50 transition-colors"
            >
              <div className="text-xs text-neon-blue font-mono mb-2">{tech.cat}</div>
              <div className="text-lg font-bold text-white mb-1">{tech.name}</div>
              <div className="text-xs text-gray-500">{tech.desc}</div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
};

export default TechStack;
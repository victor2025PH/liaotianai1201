import React from 'react';
import { Send, Mail, MessageSquare, Twitter } from 'lucide-react';
import { config } from '../src/config';

const TelegramIcon = ({ className }: { className?: string }) => (
  <svg className={className} viewBox="0 0 24 24" fill="currentColor">
    <path d="M12 0C5.373 0 0 5.373 0 12s5.373 12 12 12 12-5.373 12-12S18.627 0 12 0zm5.894 8.221l-1.97 9.28c-.145.658-.537.818-1.084.508l-3-2.21-1.446 1.394c-.14.18-.357.295-.6.295-.002 0-.003 0-.005 0l.213-3.054 5.56-5.022c.24-.213-.054-.334-.373-.12l-6.87 4.326-2.96-.924c-.64-.203-.658-.64.135-.954l11.566-4.458c.538-.196 1.006.128.832.941z"/>
  </svg>
);

const WhatsAppIcon = ({ className }: { className?: string }) => (
  <svg className={className} viewBox="0 0 24 24" fill="currentColor">
    <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413Z"/>
  </svg>
);

const Footer: React.FC = () => {
  return (
    <footer id="contact" className="bg-black border-t border-dark-border pt-20 pb-10">
      <div className="container mx-auto px-4">
        
        <div className="max-w-4xl mx-auto text-center mb-16">
          <h2 className="text-3xl md:text-5xl font-bold mb-6 tracking-tight">
            想法很贵，执行更贵。<br />
            <span className="text-gray-500">但找对人，其实很便宜。</span>
          </h2>
          <p className="text-gray-400 mb-10 text-lg">
            您的竞争对手正在研究 TON 生态。现在联系我们，获取一份免费的<span className="text-neon-blue">《Mini App 架构设计图》</span>与<span className="text-neon-purple">《裂变路径规划》</span>。
          </p>
          
          <div className="flex flex-col md:flex-row justify-center gap-6 mb-12">
            <a 
              href={config.contact.telegram} 
              target="_blank" 
              rel="noopener noreferrer" 
              data-robot-avoid="true"
              className="flex items-center justify-center gap-3 bg-[#229ED9] text-white px-8 py-4 rounded-xl font-bold hover:bg-[#1a8bc0] transition-colors"
            >
              <Send className="w-5 h-5" />
              Telegram: @ai_zkw
            </a>
            <a 
              href={`mailto:${config.contact.email}`}
              data-robot-avoid="true"
              className="flex items-center justify-center gap-3 bg-white/10 text-white px-8 py-4 rounded-xl font-bold hover:bg-white/20 transition-colors"
            >
              <Mail className="w-5 h-5" />
              Email: {config.contact.email}
            </a>
          </div>

          {/* Contact Icons - Cyberpunk Style */}
          <div className="flex flex-wrap justify-center gap-4">
            <a 
              href={config.contact.telegram} 
              target="_blank" 
              rel="noopener noreferrer" 
              data-robot-avoid="true"
              className="group flex flex-col items-center justify-center w-20 h-20 bg-zinc-900/50 border border-neon-blue/30 hover:border-neon-blue hover:bg-neon-blue/10 transition-all duration-300 backdrop-blur-sm"
            >
              <TelegramIcon className="w-6 h-6 text-zinc-400 group-hover:text-neon-blue mb-2 transition-colors" />
              <span className="text-[9px] font-mono text-zinc-600 group-hover:text-neon-blue font-bold">TG</span>
            </a>

            <a 
              href={`mailto:${config.contact.email}`} 
              data-robot-avoid="true"
              className="group flex flex-col items-center justify-center w-20 h-20 bg-zinc-900/50 border border-neon-purple/30 hover:border-neon-purple hover:bg-neon-purple/10 transition-all duration-300 backdrop-blur-sm"
            >
              <Mail className="w-6 h-6 text-zinc-400 group-hover:text-neon-purple mb-2 transition-colors" />
              <span className="text-[9px] font-mono text-zinc-600 group-hover:text-neon-purple font-bold">MAIL</span>
            </a>

            <a 
              href={config.contact.whatsapp} 
              target="_blank" 
              rel="noopener noreferrer" 
              data-robot-avoid="true"
              className="group flex flex-col items-center justify-center w-20 h-20 bg-zinc-900/50 border border-neon-green/30 hover:border-neon-green hover:bg-neon-green/10 transition-all duration-300 backdrop-blur-sm"
            >
              <WhatsAppIcon className="w-6 h-6 text-zinc-400 group-hover:text-neon-green mb-2 transition-colors" />
              <span className="text-[9px] font-mono text-zinc-600 group-hover:text-neon-green font-bold">WA</span>
            </a>

            <a 
              href={config.contact.twitter} 
              target="_blank" 
              rel="noopener noreferrer" 
              data-robot-avoid="true"
              className="group flex flex-col items-center justify-center w-20 h-20 bg-zinc-900/50 border border-white/20 hover:border-white hover:bg-white/5 transition-all duration-300 backdrop-blur-sm"
            >
              <Twitter className="w-6 h-6 text-zinc-400 group-hover:text-white mb-2 transition-colors" />
              <span className="text-[9px] font-mono text-zinc-600 group-hover:text-white font-bold">X</span>
            </a>
          </div>
        </div>

        <div className="border-t border-white/5 pt-8 text-center text-gray-600 text-sm">
          <p>&copy; {new Date().getFullYear()} TON Mini App Studio. All rights reserved.</p>
          <div className="mt-2 flex justify-center gap-4">
             <a href="#" className="hover:text-gray-400">Privacy Policy</a>
             <a href="#" className="hover:text-gray-400">Terms of Service</a>
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
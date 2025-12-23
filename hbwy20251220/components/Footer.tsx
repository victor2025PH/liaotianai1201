import React from 'react';
import { ArrowRight, MessageCircle, Send, Mail, MessageSquare, Twitter } from 'lucide-react';
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

export const Footer = () => {
  return (
    <footer className="relative py-24 overflow-hidden bg-black">
      {/* Background Glow */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[400px] bg-orange-500/10 blur-[100px] rounded-full pointer-events-none" />

      <div className="max-w-4xl mx-auto px-6 text-center relative z-10">
        <h2 className="text-4xl md:text-6xl font-display font-black mb-8">
          流量风口不等人
        </h2>
        <p className="text-xl text-gray-400 mb-12 max-w-2xl mx-auto">
          今天就开始构建您的"流量印钞机"。提供玩法策划、UI设计、合约开发到上线部署的全案服务。
        </p>
        
        <a 
          href={config.contact.telegram}
          target="_blank"
          rel="noopener noreferrer"
          data-robot-avoid="true"
          className="group relative inline-flex items-center gap-3 px-10 py-5 bg-white text-black text-lg font-bold rounded-full hover:bg-gray-200 transition-colors shadow-2xl shadow-white/10"
        >
          <MessageCircle className="w-6 h-6" />
          <span>联系产品专家，定制红包方案</span>
          <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
        </a>

        {/* Contact Icons - Game Style */}
        <div className="mt-16 flex flex-wrap justify-center gap-4">
          <a 
            href={config.contact.telegram} 
            target="_blank" 
            rel="noopener noreferrer" 
            data-robot-avoid="true"
            className="group flex flex-col items-center justify-center w-20 h-20 bg-zinc-900 border-2 border-zinc-800 hover:border-orange-500 hover:bg-orange-500/10 transition-all duration-300 rounded-lg"
          >
            <TelegramIcon className="w-6 h-6 text-zinc-400 group-hover:text-orange-500 mb-2 transition-colors" />
            <span className="text-[9px] font-mono text-zinc-600 group-hover:text-orange-500 font-bold">TG</span>
          </a>

          <a 
            href={`mailto:${config.contact.email}`} 
            data-robot-avoid="true"
            className="group flex flex-col items-center justify-center w-20 h-20 bg-zinc-900 border-2 border-zinc-800 hover:border-orange-500 hover:bg-orange-500/10 transition-all duration-300 rounded-lg"
          >
            <Mail className="w-6 h-6 text-zinc-400 group-hover:text-orange-500 mb-2 transition-colors" />
            <span className="text-[9px] font-mono text-zinc-600 group-hover:text-orange-500 font-bold">MAIL</span>
          </a>

          <a 
            href={config.contact.whatsapp} 
            target="_blank" 
            rel="noopener noreferrer" 
            data-robot-avoid="true"
            className="group flex flex-col items-center justify-center w-20 h-20 bg-zinc-900 border-2 border-zinc-800 hover:border-orange-500 hover:bg-orange-500/10 transition-all duration-300 rounded-lg"
          >
            <WhatsAppIcon className="w-6 h-6 text-zinc-400 group-hover:text-orange-500 mb-2 transition-colors" />
            <span className="text-[9px] font-mono text-zinc-600 group-hover:text-orange-500 font-bold">WA</span>
          </a>

          <a 
            href={config.contact.twitter} 
            target="_blank" 
            rel="noopener noreferrer" 
            data-robot-avoid="true"
            className="group flex flex-col items-center justify-center w-20 h-20 bg-zinc-900 border-2 border-zinc-800 hover:border-orange-500 hover:bg-orange-500/10 transition-all duration-300 rounded-lg"
          >
            <Twitter className="w-6 h-6 text-zinc-400 group-hover:text-orange-500 mb-2 transition-colors" />
            <span className="text-[9px] font-mono text-zinc-600 group-hover:text-orange-500 font-bold">X</span>
          </a>
        </div>

        <div className="mt-20 pt-10 border-t border-white/5 flex flex-col md:flex-row items-center justify-between text-gray-500 text-sm">
          <p>© 2024 RedEnvelope.fi Solutions.</p>
          <div className="flex gap-8 mt-4 md:mt-0 font-medium">
            <a href="#" className="hover:text-white transition-colors">Privacy</a>
            <a href="#" className="hover:text-white transition-colors">Terms</a>
            <a href={config.contact.telegram} target="_blank" rel="noopener noreferrer" className="hover:text-white transition-colors">Telegram Channel</a>
          </div>
        </div>
      </div>
    </footer>
  );
};
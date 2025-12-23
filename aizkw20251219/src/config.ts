/**
 * 項目配置檔案
 * 集中管理所有硬編碼的配置信息
 */

export const config = {
  // 項目基本信息
  project: {
    name: 'Smart Control King | AI 智控王',
    nameShort: 'SCK',
    version: '0.0.0',
    systemId: '8492-AX',
  },

  // 聯繫方式
  contact: {
    email: 'victor2018zzz@gmail.com',
    telegram: 'https://t.me/ai_zkw', // Telegram: @ai_zkw (ID: 5433982810)
    whatsapp: 'https://wa.me/639273815533', // WhatsApp: +639273815533
    twitter: 'https://x.com/victor242490199', // X (Twitter): @victor242490199
  },

  // 部署配置
  deploy: {
    serverPath: '/home/ubuntu/aizkw20251219',
    buildCommand: 'npm run build',
    installCommand: 'npm install',
  },

  // AI 配置
  ai: {
    // 优先使用 OpenAI，如果没有则使用 Gemini
    provider: 'openai', // 'openai' | 'gemini'
    openaiModel: 'gpt-4o-mini',
    geminiModel: 'gemini-2.5-flash-latest',
  },
} as const;

export default config;


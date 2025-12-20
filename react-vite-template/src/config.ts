/**
 * 網站全局配置
 * 統一管理所有聯繫方式、Logo 路徑、項目名稱等配置
 * 修改此文件即可更新全站的聯繫方式
 */

export interface SiteConfig {
  // 項目基本信息
  projectName: string;
  projectDescription: string;
  
  // 聯繫方式
  contact: {
    telegram: {
      username: string;
      url: string;
      displayName: string;
    };
    whatsapp: {
      number: string;
      url: string;
      displayName: string;
    };
    email: {
      address: string;
      displayName: string;
    };
    phone?: {
      number: string;
      displayName: string;
    };
  };
  
  // Logo 和品牌
  branding: {
    logoPath: string;
    faviconPath: string;
    companyName: string;
  };
  
  // 社交媒體（可選）
  social?: {
    twitter?: string;
    facebook?: string;
    linkedin?: string;
    github?: string;
  };
}

// 默認配置 - 請根據實際項目修改
export const siteConfig: SiteConfig = {
  projectName: "AIZKW",
  projectDescription: "智能 AI 系統管理平台",
  
  contact: {
    telegram: {
      username: "@your_telegram_username",
      url: "https://t.me/your_telegram_username",
      displayName: "Telegram 客服",
    },
    whatsapp: {
      number: "+1234567890",
      url: "https://wa.me/1234567890",
      displayName: "WhatsApp 客服",
    },
    email: {
      address: "support@example.com",
      displayName: "support@example.com",
    },
    phone: {
      number: "+1234567890",
      displayName: "+1234567890",
    },
  },
  
  branding: {
    logoPath: "/logo.png",
    faviconPath: "/favicon.ico",
    companyName: "Your Company Name",
  },
  
  social: {
    twitter: "https://twitter.com/your_handle",
    facebook: "https://facebook.com/your_page",
    linkedin: "https://linkedin.com/company/your_company",
    github: "https://github.com/your_username",
  },
};

// 導出便捷訪問函數
export const getTelegramUrl = () => siteConfig.contact.telegram.url;
export const getWhatsAppUrl = () => siteConfig.contact.whatsapp.url;
export const getEmailAddress = () => siteConfig.contact.email.address;
export const getLogoPath = () => siteConfig.branding.logoPath;
export const getProjectName = () => siteConfig.projectName;

// 默認導出
export default siteConfig;

/**
 * AI 配置工具
 * 统一从后端 API 获取 AI KEY
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'https://aiadmin.usdt2026.cc';

let cachedConfig: {
  openai_api_key: string;
  gemini_api_key: string;
  default_language: string;
  ai_model: string;
} | null = null;

let configPromise: Promise<typeof cachedConfig> | null = null;

/**
 * 从后端获取 AI 配置
 */
export async function getAIConfig(): Promise<{
  openai_api_key: string;
  gemini_api_key: string;
  default_language: string;
  ai_model: string;
}> {
  if (cachedConfig) {
    return cachedConfig;
  }

  if (configPromise) {
    return configPromise;
  }

  configPromise = (async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/frontend-config/ai-keys`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`获取 AI 配置失败: ${response.status}`);
      }

      const config = await response.json();
      cachedConfig = config;
      return config;
    } catch (error) {
      console.error('获取 AI 配置失败:', error);
      return {
        openai_api_key: import.meta.env.VITE_OPENAI_API_KEY || '',
        gemini_api_key: import.meta.env.VITE_GEMINI_API_KEY || '',
        default_language: 'zh-CN',
        ai_model: 'gpt-4o-mini',
      };
    }
  })();

  return configPromise;
}

/**
 * 检测用户输入的语言
 * 如果不是明确的英文或其他语言，返回中文
 */
export function detectUserLanguage(text: string): 'zh-CN' | 'en' {
  const englishChars = (text.match(/[a-zA-Z]/g) || []).length;
  const totalChars = text.length;
  const englishRatio = totalChars > 0 ? englishChars / totalChars : 0;

  if (englishRatio > 0.7 && totalChars > 5) {
    return 'en';
  }

  return 'zh-CN';
}

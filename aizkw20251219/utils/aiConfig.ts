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
  // 如果已有缓存，直接返回
  if (cachedConfig) {
    return cachedConfig;
  }

  // 如果正在请求，等待请求完成
  if (configPromise) {
    return configPromise;
  }

  // 发起请求
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
      // 返回空配置，使用环境变量作为后备
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
  // 简单的语言检测：如果包含大量英文字符，可能是英文
  const englishChars = (text.match(/[a-zA-Z]/g) || []).length;
  const totalChars = text.length;
  const englishRatio = totalChars > 0 ? englishChars / totalChars : 0;

  // 如果英文比例超过 70%，且总长度超过 5 个字符，认为是英文
  if (englishRatio > 0.7 && totalChars > 5) {
    return 'en';
  }

  // 默认使用中文
  return 'zh-CN';
}

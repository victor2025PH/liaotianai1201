/**
 * 統一的 API 配置
 * 所有 API 調用都應該使用這個配置文件中的常量
 */

/**
 * API 基礎 URL
 * 優先使用環境變量 NEXT_PUBLIC_API_BASE_URL
 * 如果未設置，則根據當前環境自動判斷
 */
export function getApiBaseUrl(): string {
  // 優先使用環境變量
  if (process.env.NEXT_PUBLIC_API_BASE_URL) {
    return process.env.NEXT_PUBLIC_API_BASE_URL;
  }

  // 如果是在瀏覽器環境
  if (typeof window !== "undefined") {
    const host = window.location.host;
    const protocol = window.location.protocol;
    
    // 開發環境：localhost 使用 8000 端口
    if (host.includes("localhost") || host.includes("127.0.0.1")) {
      return "http://localhost:8000/api/v1";
    }
    
    // 生產環境：使用相對路徑，讓 Nginx 處理代理
    // 這樣可以避免 CORS 問題，並且讓 Nginx 正確代理到後端
    // 使用當前協議和主機，確保在生產環境中正確工作
    return `${protocol}//${host}/api/v1`;
  }

  // 服務端渲染：檢查是否在生產環境
  // 如果是生產環境，使用相對路徑
  if (process.env.NODE_ENV === "production") {
    // 在生產環境中，如果沒有設置環境變量，使用相對路徑
    // 這樣 Next.js 在服務端渲染時會使用當前請求的 host
    return "/api/v1";
  }

  // 開發環境：使用默認值
  return "http://localhost:8000/api/v1";
}

/**
 * Group AI API 基礎 URL
 * 用於群組 AI 相關的 API 調用
 */
export function getGroupAiApiBaseUrl(): string {
  const baseUrl = getApiBaseUrl();
  // 如果 baseUrl 已經包含 /group-ai，直接返回
  if (baseUrl.endsWith("/group-ai")) {
    return baseUrl;
  }
  // 否則追加 /group-ai
  return `${baseUrl}/group-ai`;
}

/**
 * WebSocket URL
 * 用於 WebSocket 連接
 */
export function getWebSocketUrl(): string {
  // 優先使用環境變量
  if (process.env.NEXT_PUBLIC_WS_URL) {
    return process.env.NEXT_PUBLIC_WS_URL;
  }

  // 如果是在瀏覽器環境
  if (typeof window !== "undefined") {
    const host = window.location.host;
    
    // 開發環境：localhost 使用 8000 端口
    if (host.includes("localhost") || host.includes("127.0.0.1")) {
      return "ws://localhost:8000/api/v1/notifications/ws";
    }
    
    // 生產環境：使用當前域名
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    return `${protocol}//${host}/api/v1/notifications/ws`;
  }

  // 默認值
  return "ws://localhost:8000/api/v1/notifications/ws";
}

// 導出常量（為了向後兼容）
// 注意：這些常量在模塊加載時計算，可能導致 SSR 問題
// 如果遇到 "location is not defined" 錯誤，請使用函數版本
export const API_BASE_URL = typeof window !== "undefined" ? getApiBaseUrl() : "/api/v1";
export const GROUP_AI_API_BASE_URL = typeof window !== "undefined" ? getGroupAiApiBaseUrl() : "/api/v1/group-ai";
export const WS_URL = typeof window !== "undefined" ? getWebSocketUrl() : "ws://localhost:8000/api/v1/notifications/ws";


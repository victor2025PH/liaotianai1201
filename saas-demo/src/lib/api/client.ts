/**
 * API 客戶端工具函數
 */

import { getToken } from "./auth"

/**
 * 獲取帶有認證頭的請求配置
 */
export function getAuthHeaders(): HeadersInit {
  const token = getToken()
  const headers: HeadersInit = {
    "Content-Type": "application/json",
  }
  
  if (token) {
    headers["Authorization"] = `Bearer ${token}`
  }
  
  return headers
}

/**
 * 帶認證的 fetch 請求
 */
export async function fetchWithAuth(
  url: string,
  options: RequestInit = {}
): Promise<Response> {
  const headers = new Headers(options.headers)
  
  // 添加認證頭
  const authHeaders = getAuthHeaders()
  Object.entries(authHeaders).forEach(([key, value]) => {
    headers.set(key, value)
  })
  
  // 合併自定義 headers
  if (options.headers) {
    Object.entries(options.headers).forEach(([key, value]) => {
      headers.set(key, value as string)
    })
  }
  
  const response = await fetch(url, {
    ...options,
    headers,
  })
  
  // 處理 401 未授權錯誤：自動清除 token 並重定向到登錄頁
  if (response.status === 401) {
    // 清除過期的 token
    if (typeof window !== "undefined") {
      localStorage.removeItem("access_token")
      // 觸發 token 清除事件
      window.dispatchEvent(new Event("tokenCleared"))
      
      // 如果不在登錄頁，重定向到登錄頁
      if (window.location.pathname !== "/login") {
        console.warn("[API] Token 已過期或無效，正在重定向到登錄頁...")
        window.location.href = "/login"
      }
    }
  }
  
  return response
}


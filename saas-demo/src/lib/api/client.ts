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
  
  return fetch(url, {
    ...options,
    headers,
  })
}


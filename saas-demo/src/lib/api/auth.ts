/**
 * 認證 API 客戶端
 */

import { getApiBaseUrl } from "./config";

const API_BASE = getApiBaseUrl();

export interface LoginRequest {
  username: string // 郵箱
  password: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
}

export interface User {
  email: string
  is_active: boolean
  is_superuser: boolean
}

/**
 * 登錄
 */
export async function login(credentials: LoginRequest): Promise<TokenResponse> {
  try {
    const formData = new URLSearchParams()
    formData.append("username", credentials.username)
    formData.append("password", credentials.password)

    const response = await fetch(`${API_BASE}/auth/login`, {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
      },
      body: formData.toString(),
    })

    if (!response.ok) {
      let errorMessage = `HTTP ${response.status}`
      try {
        const error = await response.json()
        errorMessage = error.detail || error.message || errorMessage
      } catch {
        // 如果無法解析 JSON，使用默認錯誤消息
        if (response.status === 401) {
          errorMessage = "郵箱或密碼錯誤"
        } else if (response.status === 404) {
          errorMessage = "登錄接口不可用，請檢查後端服務是否運行"
        } else if (response.status >= 500) {
          errorMessage = "服務器錯誤，請稍後再試"
        }
      }
      throw new Error(errorMessage)
    }

    return response.json()
  } catch (error) {
    // 網絡錯誤
    if (error instanceof TypeError && error.message.includes("fetch")) {
      console.error("[API] 網絡錯誤，無法連接到後端服務（登錄 API）")
      throw new Error(`無法連接到後端服務，請檢查服務是否運行（${API_BASE}）`)
    }
    // 重新拋出其他錯誤
    throw error
  }
}

/**
 * 登出（清除本地存儲的 token）
 * @param redirect 是否重定向到登入頁（默認 true）
 */
export function logout(redirect: boolean = true): void {
  if (typeof window !== "undefined") {
    localStorage.removeItem("access_token")
    // 觸發自定義事件，通知其他組件 token 已被清除
    window.dispatchEvent(new Event("tokenCleared"))
    if (redirect && window.location.pathname !== "/login") {
      window.location.href = "/login"
    }
  }
}

/**
 * 獲取存儲的 token
 */
export function getToken(): string | null {
  if (typeof window === "undefined") return null
  return localStorage.getItem("access_token")
}

/**
 * 保存 token
 */
export function setToken(token: string): void {
  if (typeof window !== "undefined") {
    localStorage.setItem("access_token", token)
  }
}

/**
 * 檢查是否已登錄
 */
export function isAuthenticated(): boolean {
  return getToken() !== null
}


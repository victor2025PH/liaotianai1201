/**
 * 用戶管理 API 客戶端
 */

import { fetchWithAuth } from "./client"

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000/api/v1"

export interface User {
  id: number
  email: string
  full_name?: string
  is_active: boolean
  is_superuser: boolean
  roles: Role[]
  created_at: string
}

export interface Role {
  id: number
  name: string
}

export interface UserCreate {
  email: string
  password: string
  full_name?: string
  is_active?: boolean
  is_superuser?: boolean
}

export interface UserUpdate {
  email?: string
  full_name?: string
  is_active?: boolean
  is_superuser?: boolean
}

export interface UserPasswordReset {
  new_password: string
}

/**
 * 獲取當前用戶信息
 */
export async function getCurrentUser(): Promise<User> {
  const response = await fetchWithAuth(`${API_BASE}/users/me`, {
    credentials: "include",
  })
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`)
  }
  return response.json()
}

/**
 * 列出所有用戶
 */
export async function listAllUsers(): Promise<User[]> {
  const response = await fetchWithAuth(`${API_BASE}/users/`, {
    credentials: "include",
  })
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`)
  }
  return response.json()
}

/**
 * 創建新用戶
 */
export async function createUser(user: UserCreate): Promise<User> {
  const response = await fetchWithAuth(`${API_BASE}/users/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    credentials: "include",
    body: JSON.stringify(user),
  })
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: `HTTP ${response.status}` }))
    throw new Error(error.detail || `HTTP ${response.status}`)
  }
  return response.json()
}

/**
 * 更新用戶信息
 */
export async function updateUser(userId: number, user: UserUpdate): Promise<User> {
  const response = await fetchWithAuth(`${API_BASE}/users/${userId}`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
    },
    credentials: "include",
    body: JSON.stringify(user),
  })
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: `HTTP ${response.status}` }))
    throw new Error(error.detail || `HTTP ${response.status}`)
  }
  return response.json()
}

/**
 * 刪除用戶
 */
export async function deleteUser(userId: number): Promise<{ message: string }> {
  const response = await fetchWithAuth(`${API_BASE}/users/${userId}`, {
    method: "DELETE",
    credentials: "include",
  })
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: `HTTP ${response.status}` }))
    throw new Error(error.detail || `HTTP ${response.status}`)
  }
  return response.json()
}

/**
 * 重置用戶密碼
 */
export async function resetUserPassword(
  userId: number,
  passwordReset: UserPasswordReset
): Promise<{ message: string }> {
  const response = await fetchWithAuth(`${API_BASE}/users/${userId}/reset-password`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    credentials: "include",
    body: JSON.stringify(passwordReset),
  })
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: `HTTP ${response.status}` }))
    throw new Error(error.detail || `HTTP ${response.status}`)
  }
  return response.json()
}


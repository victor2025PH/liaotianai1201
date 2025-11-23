/**
 * 用戶角色管理 API 客戶端
 */

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000/api/v1"

export interface User {
  id: number
  email: string
  full_name?: string
  is_active: boolean
  is_superuser: boolean
  roles: Role[]
}

export interface Role {
  id: number
  name: string
  description?: string
}

export interface UserRoleAssign {
  role_name: string
}

export interface BatchRoleAssign {
  user_ids: number[]
  role_name: string
}

export interface BatchRoleRevoke {
  user_ids: number[]
  role_name: string
}

export interface BatchOperationResult {
  success_count: number
  failed_count: number
  errors: string[]
}

/**
 * 列出所有用戶及其角色
 */
export async function listUsers(): Promise<User[]> {
  const response = await fetch(`${API_BASE}/user-roles/users`)
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`)
  }
  return response.json()
}

/**
 * 獲取用戶詳情
 */
export async function getUser(userId: number): Promise<User> {
  const response = await fetch(`${API_BASE}/user-roles/users/${userId}`)
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`)
  }
  return response.json()
}

/**
 * 為用戶分配角色
 */
export async function assignRoleToUser(
  userId: number,
  assign: UserRoleAssign
): Promise<{ message: string }> {
  const response = await fetch(`${API_BASE}/user-roles/users/${userId}/roles`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(assign),
  })
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`)
  }
  return response.json()
}

/**
 * 從用戶撤銷角色
 */
export async function revokeRoleFromUser(
  userId: number,
  roleName: string
): Promise<{ message: string }> {
  const response = await fetch(`${API_BASE}/user-roles/users/${userId}/roles/${roleName}`, {
    method: "DELETE",
  })
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`)
  }
  return response.json()
}

/**
 * 獲取用戶的所有角色
 */
export async function getUserRoles(userId: number): Promise<Role[]> {
  const response = await fetch(`${API_BASE}/user-roles/users/${userId}/roles`)
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`)
  }
  return response.json()
}

/**
 * 批量為用戶分配角色
 */
export async function batchAssignRole(
  batch: BatchRoleAssign
): Promise<BatchOperationResult> {
  const response = await fetch(`${API_BASE}/user-roles/batch-assign`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(batch),
  })
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: `HTTP ${response.status}` }))
    throw new Error(error.detail || `HTTP ${response.status}`)
  }
  return response.json()
}

/**
 * 批量從用戶撤銷角色
 */
export async function batchRevokeRole(
  batch: BatchRoleRevoke
): Promise<BatchOperationResult> {
  const response = await fetch(`${API_BASE}/user-roles/batch-revoke`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(batch),
  })
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: `HTTP ${response.status}` }))
    throw new Error(error.detail || `HTTP ${response.status}`)
  }
  return response.json()
}


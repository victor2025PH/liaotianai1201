/**
 * 權限管理 API 客戶端
 */

import { getApiBaseUrl } from "./config";

const API_BASE = getApiBaseUrl();

export interface Permission {
  id: number
  code: string
  description?: string
}

export interface PermissionCreate {
  code: string
  description?: string
}

export interface PermissionUpdate {
  code?: string
  description?: string
}

export interface RolePermissionAssign {
  permission_code: string
}

export interface UserPermissionCheck {
  permission_code: string
}

export interface UserPermissionCheckResponse {
  has_permission: boolean
  permission_code: string
  user_email: string
}

/**
 * 創建權限
 */
export async function createPermission(permission: PermissionCreate): Promise<Permission> {
  const { fetchWithAuth } = await import("./client")
  const response = await fetchWithAuth(`${API_BASE}/permissions`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(permission),
  })
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`)
  }
  return response.json()
}

/**
 * 列出所有權限
 */
export async function listPermissions(params?: {
  skip?: number
  limit?: number
}): Promise<Permission[]> {
  const { fetchWithAuth } = await import("./client")
  const urlParams = new URLSearchParams()
  if (params?.skip) urlParams.append("skip", params.skip.toString())
  if (params?.limit) urlParams.append("limit", params.limit.toString())
  
  const response = await fetchWithAuth(`${API_BASE}/permissions?${urlParams}`)
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`)
  }
  return response.json()
}

/**
 * 獲取權限詳情
 */
export async function getPermission(permissionId: number): Promise<Permission> {
  const { fetchWithAuth } = await import("./client")
  const response = await fetchWithAuth(`${API_BASE}/permissions/${permissionId}`)
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`)
  }
  return response.json()
}

/**
 * 更新權限
 */
export async function updatePermission(
  permissionId: number,
  update: PermissionUpdate
): Promise<Permission> {
  const { fetchWithAuth } = await import("./client")
  const response = await fetchWithAuth(`${API_BASE}/permissions/${permissionId}`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(update),
  })
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`)
  }
  return response.json()
}

/**
 * 刪除權限
 */
export async function deletePermission(permissionId: number): Promise<void> {
  const { fetchWithAuth } = await import("./client")
  const response = await fetchWithAuth(`${API_BASE}/permissions/${permissionId}`, {
    method: "DELETE",
  })
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`)
  }
}

/**
 * 為角色分配權限
 */
export async function assignPermissionToRole(
  roleName: string,
  assign: RolePermissionAssign
): Promise<{ message: string }> {
  const { fetchWithAuth } = await import("./client")
  const response = await fetchWithAuth(`${API_BASE}/permissions/roles/${roleName}/permissions`, {
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
 * 從角色撤銷權限
 */
export async function revokePermissionFromRole(
  roleName: string,
  permissionCode: string
): Promise<{ message: string }> {
  const { fetchWithAuth } = await import("./client")
  const response = await fetchWithAuth(`${API_BASE}/permissions/roles/${roleName}/permissions/${permissionCode}`, {
    method: "DELETE",
  })
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`)
  }
  return response.json()
}

/**
 * 獲取角色的所有權限
 */
export async function getRolePermissions(roleName: string): Promise<Permission[]> {
  const { fetchWithAuth } = await import("./client")
  const response = await fetchWithAuth(`${API_BASE}/permissions/roles/${roleName}/permissions`)
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`)
  }
  return response.json()
}

/**
 * 獲取當前用戶的所有權限
 */
export async function getMyPermissions(): Promise<Permission[]> {
  const { fetchWithAuth } = await import("./client")
  const response = await fetchWithAuth(`${API_BASE}/permissions/me/permissions`)
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`)
  }
  return response.json()
}

/**
 * 檢查當前用戶是否有指定權限
 */
export async function checkMyPermission(
  check: UserPermissionCheck
): Promise<UserPermissionCheckResponse> {
  const { fetchWithAuth } = await import("./client")
  const response = await fetchWithAuth(`${API_BASE}/permissions/me/check`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(check),
  })
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`)
  }
  return response.json()
}

/**
 * 初始化系統權限
 */
export async function initPermissions(): Promise<{ message: string; permissions_created: number; roles_created: number }> {
  const { fetchWithAuth } = await import("./client")
  const response = await fetchWithAuth(`${API_BASE}/permissions/init`, {
    method: "POST",
  })
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`)
  }
  return response.json()
}


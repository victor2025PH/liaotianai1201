/**
 * 角色管理 API 客戶端
 */

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000/api/v1"

export interface Role {
  id: number
  name: string
  description?: string
}

export interface RoleWithPermissions extends Role {
  permissions: Permission[]
}

export interface Permission {
  id: number
  code: string
  description?: string
}

export interface RoleCreate {
  name: string
  description?: string
}

export interface RoleUpdate {
  name?: string
  description?: string
}

export interface RolePermissionAssign {
  permission_code: string
}

/**
 * 創建角色
 */
export async function createRole(role: RoleCreate): Promise<Role> {
  const response = await fetch(`${API_BASE}/roles`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(role),
  })
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`)
  }
  return response.json()
}

/**
 * 列出所有角色
 */
export async function listRoles(): Promise<Role[]> {
  const response = await fetch(`${API_BASE}/roles`)
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`)
  }
  return response.json()
}

/**
 * 獲取角色詳情
 */
export async function getRole(roleId: number): Promise<RoleWithPermissions> {
  const response = await fetch(`${API_BASE}/roles/${roleId}`)
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`)
  }
  return response.json()
}

/**
 * 更新角色
 */
export async function updateRole(
  roleId: number,
  update: RoleUpdate
): Promise<Role> {
  const response = await fetch(`${API_BASE}/roles/${roleId}`, {
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
 * 刪除角色
 */
export async function deleteRole(roleId: number): Promise<void> {
  const response = await fetch(`${API_BASE}/roles/${roleId}`, {
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
  roleId: number,
  assign: RolePermissionAssign
): Promise<{ message: string }> {
  const response = await fetch(`${API_BASE}/roles/${roleId}/permissions`, {
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
  roleId: number,
  permissionCode: string
): Promise<{ message: string }> {
  const response = await fetch(`${API_BASE}/roles/${roleId}/permissions/${permissionCode}`, {
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
export async function getRolePermissions(roleId: number): Promise<Permission[]> {
  const response = await fetch(`${API_BASE}/roles/${roleId}/permissions`)
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`)
  }
  return response.json()
}


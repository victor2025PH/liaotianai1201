/**
 * 權限守衛組件 - 根據權限顯示/隱藏內容
 */
"use client"

import { ReactNode } from "react"
import { usePermissions } from "@/hooks/use-permissions"

interface PermissionGuardProps {
  /** 需要的權限代碼 */
  permission: string
  /** 是否需要所有權限（默認：false，任意一個即可） */
  requireAll?: boolean
  /** 沒有權限時顯示的內容 */
  fallback?: ReactNode
  /** 子組件 */
  children: ReactNode
}

export function PermissionGuard({
  permission,
  requireAll = false,
  fallback = null,
  children,
}: PermissionGuardProps) {
  const { hasPermission, loading } = usePermissions()

  if (loading) {
    return null // 加載中不顯示任何內容
  }

  if (requireAll) {
    // 需要所有權限（單個權限時等同於 hasPermission）
    if (!hasPermission(permission)) {
      return <>{fallback}</>
    }
  } else {
    // 需要任意一個權限
    if (!hasPermission(permission)) {
      return <>{fallback}</>
    }
  }

  return <>{children}</>
}

interface MultiplePermissionGuardProps {
  /** 需要的權限代碼列表 */
  permissions: string[]
  /** 是否需要所有權限（默認：false，任意一個即可） */
  requireAll?: boolean
  /** 沒有權限時顯示的內容 */
  fallback?: ReactNode
  /** 子組件 */
  children: ReactNode
}

export function MultiplePermissionGuard({
  permissions,
  requireAll = false,
  fallback = null,
  children,
}: MultiplePermissionGuardProps) {
  const { hasAnyPermission, hasAllPermissions, loading } = usePermissions()

  if (loading) {
    return null // 加載中不顯示任何內容
  }

  const hasPermission = requireAll
    ? hasAllPermissions(permissions)
    : hasAnyPermission(permissions)

  if (!hasPermission) {
    return <>{fallback}</>
  }

  return <>{children}</>
}


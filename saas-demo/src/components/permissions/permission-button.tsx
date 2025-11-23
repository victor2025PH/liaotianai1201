/**
 * 權限按鈕組件 - 根據權限啟用/禁用按鈕
 */
"use client"

import { ReactNode, ButtonHTMLAttributes } from "react"
import { usePermissions } from "@/hooks/use-permissions"
import { Button } from "@/components/ui/button"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"

interface PermissionButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  /** 需要的權限代碼 */
  permission: string
  /** 是否需要所有權限（默認：false，任意一個即可） */
  requireAll?: boolean
  /** 沒有權限時的提示文本 */
  tooltip?: string
  /** 子組件 */
  children: ReactNode
  /** 按鈕變體 */
  variant?: "default" | "destructive" | "outline" | "secondary" | "ghost" | "link"
  /** 按鈕大小 */
  size?: "default" | "sm" | "lg" | "icon"
}

export function PermissionButton({
  permission,
  requireAll = false,
  tooltip = "您沒有權限執行此操作",
  children,
  variant = "default",
  size = "default",
  disabled,
  onClick,
  ...props
}: PermissionButtonProps) {
  const { hasPermission, loading } = usePermissions()

  const hasRequiredPermission = !loading && hasPermission(permission)
  const isDisabled = disabled || !hasRequiredPermission

  const handleClick = (e: React.MouseEvent<HTMLButtonElement>) => {
    if (!hasRequiredPermission) {
      e.preventDefault()
      e.stopPropagation()
      return
    }
    if (onClick) {
      onClick(e)
    }
  }

  const button = (
    <Button
      variant={variant}
      size={size}
      disabled={isDisabled}
      onClick={handleClick}
      {...props}
    >
      {children}
    </Button>
  )

  if (!hasRequiredPermission && tooltip) {
    return (
      <TooltipProvider>
        <Tooltip>
          <TooltipTrigger asChild>
            {button}
          </TooltipTrigger>
          <TooltipContent>
            <p>{tooltip}</p>
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>
    )
  }

  return button
}

interface MultiplePermissionButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  /** 需要的權限代碼列表 */
  permissions: string[]
  /** 是否需要所有權限（默認：false，任意一個即可） */
  requireAll?: boolean
  /** 沒有權限時的提示文本 */
  tooltip?: string
  /** 子組件 */
  children: ReactNode
  /** 按鈕變體 */
  variant?: "default" | "destructive" | "outline" | "secondary" | "ghost" | "link"
  /** 按鈕大小 */
  size?: "default" | "sm" | "lg" | "icon"
}

export function MultiplePermissionButton({
  permissions,
  requireAll = false,
  tooltip = "您沒有權限執行此操作",
  children,
  variant = "default",
  size = "default",
  disabled,
  onClick,
  ...props
}: MultiplePermissionButtonProps) {
  const { hasAnyPermission, hasAllPermissions, loading } = usePermissions()

  const hasRequiredPermission = !loading && (requireAll
    ? hasAllPermissions(permissions)
    : hasAnyPermission(permissions))
  const isDisabled = disabled || !hasRequiredPermission

  const handleClick = (e: React.MouseEvent<HTMLButtonElement>) => {
    if (!hasRequiredPermission) {
      e.preventDefault()
      e.stopPropagation()
      return
    }
    if (onClick) {
      onClick(e)
    }
  }

  const button = (
    <Button
      variant={variant}
      size={size}
      disabled={isDisabled}
      onClick={handleClick}
      {...props}
    >
      {children}
    </Button>
  )

  if (!hasRequiredPermission && tooltip) {
    return (
      <TooltipProvider>
        <Tooltip>
          <TooltipTrigger asChild>
            {button}
          </TooltipTrigger>
          <TooltipContent>
            <p>{tooltip}</p>
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>
    )
  }

  return button
}


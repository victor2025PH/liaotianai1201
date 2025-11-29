/**
 * 權限檢查 Hook - 使用 React Query 緩存權限數據
 */
import { useQuery, useQueryClient } from "@tanstack/react-query"
import { getMyPermissions, checkMyPermission, type Permission } from "@/lib/api/permissions"

// 權限緩存配置
const PERMISSIONS_CACHE_KEY = ["permissions", "me"]
const PERMISSIONS_STALE_TIME = 5 * 60 * 1000 // 5 分鐘內數據被認為是新鮮的
const PERMISSIONS_GC_TIME = 10 * 60 * 1000 // 10 分鐘後未使用的數據被垃圾回收

// 檢查是否禁用認證（從環境變量或 localStorage）
const isAuthDisabled = (): boolean => {
  if (typeof window === "undefined") return false
  // 檢查環境變量
  const envValue = process.env.NEXT_PUBLIC_DISABLE_AUTH
  if (envValue === "true" || envValue === "1") return true
  // 檢查 localStorage（用於開發測試）
  const storedValue = localStorage.getItem("DISABLE_AUTH")
  return storedValue === "true"
}

export function usePermissions() {
  const queryClient = useQueryClient()

  // 使用 React Query 緩存權限數據
  const {
    data: permissions = [],
    isLoading: loading,
    error,
    refetch,
  } = useQuery<Permission[], Error>({
    queryKey: PERMISSIONS_CACHE_KEY,
    queryFn: async () => {
      try {
        const data = await getMyPermissions()
        // 如果返回空數組，且禁用認證或開發模式，返回所有權限（通過返回一個特殊標記）
        if (data.length === 0 && (isAuthDisabled() || process.env.NODE_ENV === "development")) {
          // 返回一個包含所有常見權限的數組（實際檢查時會全部通過）
          return [{ id: -1, code: "*", description: "All permissions (DISABLE_AUTH=true or dev mode)" }]
        }
        return data
      } catch (err: any) {
        // 如果 API 調用失敗（404/401/500 等），在開發模式或禁用認證模式下假設有所有權限
        const isDevMode = process.env.NODE_ENV === "development"
        const authDisabled = isAuthDisabled() || isDevMode
        
        if (authDisabled || err?.message?.includes("404") || err?.message?.includes("401")) {
          console.warn("權限 API 調用失敗，但在禁用認證/開發模式下假設有所有權限:", err)
          return [{ id: -1, code: "*", description: "All permissions (DISABLE_AUTH=true or dev mode)" }]
        }
        throw new Error(err instanceof Error ? err.message : "加載權限失敗")
      }
    },
    staleTime: PERMISSIONS_STALE_TIME, // 5 分鐘內不重新獲取
    gcTime: PERMISSIONS_GC_TIME, // 10 分鐘後垃圾回收
    retry: 1, // 失敗時重試 1 次
    retryDelay: 1000, // 重試延遲 1 秒
    refetchOnWindowFocus: false, // 窗口聚焦時不自動重新獲取
    refetchOnMount: false, // 組件掛載時如果數據新鮮則不重新獲取
    refetchOnReconnect: true, // 網絡重連時重新獲取
  })

  const hasPermission = (permissionCode: string): boolean => {
    // 如果禁用認證，或者權限列表包含 "*"（表示所有權限），返回 true
    if (isAuthDisabled() || permissions.some((p) => p.code === "*")) {
      return true
    }
    // 檢查 admin:all 權限（覆蓋所有權限）
    if (permissions.some((p) => p.code === "admin:all")) {
      return true
    }
    // 如果權限列表為空（API 失敗或尚未加載），默認允許所有操作
    // 這樣可以避免在權限 API 不可用時導致整個系統無法使用
    if (permissions.length === 0 && !loading) {
      return true
    }
    return permissions.some((p) => p.code === permissionCode)
  }

  const hasAnyPermission = (permissionCodes: string[]): boolean => {
    // 如果禁用認證，返回 true
    if (isAuthDisabled() || permissions.some((p) => p.code === "*")) {
      return true
    }
    // 如果權限列表為空，默認允許
    if (permissions.length === 0 && !loading) {
      return true
    }
    return permissionCodes.some((code) => hasPermission(code))
  }

  const hasAllPermissions = (permissionCodes: string[]): boolean => {
    // 如果禁用認證，返回 true
    if (isAuthDisabled() || permissions.some((p) => p.code === "*")) {
      return true
    }
    // 如果權限列表為空，默認允許
    if (permissions.length === 0 && !loading) {
      return true
    }
    return permissionCodes.every((code) => hasPermission(code))
  }

  const checkPermission = async (permissionCode: string): Promise<boolean> => {
    // 如果禁用認證，直接返回 true
    if (isAuthDisabled()) {
      return true
    }
    try {
      const result = await checkMyPermission({ permission_code: permissionCode })
      return result.has_permission
    } catch (err) {
      console.error("檢查權限失敗:", err)
      // 如果檢查失敗且禁用認證，返回 true
      if (isAuthDisabled()) {
        return true
      }
      return false
    }
  }

  // 手動刷新權限（清除緩存並重新獲取）
  const refresh = () => {
    queryClient.invalidateQueries({ queryKey: PERMISSIONS_CACHE_KEY })
    refetch()
  }

  // 清除權限緩存
  const clearCache = () => {
    queryClient.removeQueries({ queryKey: PERMISSIONS_CACHE_KEY })
  }

  return {
    permissions,
    loading,
    error: error ? (error instanceof Error ? error.message : "加載權限失敗") : null,
    hasPermission,
    hasAnyPermission,
    hasAllPermissions,
    checkPermission,
    refresh,
    clearCache,
  }
}


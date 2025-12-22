/**
 * 通用 CRUD Hook - 统一管理列表、创建、更新、删除操作
 * 支持泛型，确保类型安全
 */

"use client"

import { useState, useCallback, useEffect, useRef } from "react"
import { useToast } from "@/hooks/use-toast"

// 分页信息
export interface PaginationInfo {
  page: number
  pageSize: number
  total: number
  totalPages: number
}

// 搜索和过滤
export interface SearchFilters {
  search?: string
  [key: string]: any
}

// CRUD Hook 配置
export interface UseCrudConfig<T, CreateT, UpdateT> {
  // API 函数
  listApi: (params?: any) => Promise<T[] | { items: T[], total?: number }>
  getApi?: (id: string) => Promise<T>
  createApi: (data: CreateT) => Promise<T>
  updateApi: (id: string, data: UpdateT) => Promise<T>
  deleteApi: (id: string) => Promise<void>
  
  // 初始配置
  initialFilters?: SearchFilters
  initialPagination?: {
    page?: number
    pageSize?: number
  }
  
  // 选项
  autoFetch?: boolean  // 是否自动获取列表（默认 true）
  onSuccess?: (action: "create" | "update" | "delete", data?: T) => void
  onError?: (error: Error, action: "create" | "update" | "delete") => void
}

// CRUD Hook 返回值
export interface UseCrudReturn<T, CreateT, UpdateT> {
  // 数据
  items: T[]
  item: T | null
  loading: boolean
  error: string | null
  
  // 分页
  pagination: PaginationInfo
  setPagination: (pagination: Partial<PaginationInfo> | ((prev: PaginationInfo) => Partial<PaginationInfo>)) => void
  
  // 搜索和过滤
  filters: SearchFilters
  setFilters: (filters: SearchFilters | ((prev: SearchFilters) => SearchFilters)) => void
  resetFilters: () => void
  
  // CRUD 操作
  fetchItems: () => Promise<void>
  getItem: (id: string) => Promise<T | null>
  createItem: (data: CreateT) => Promise<T | null>
  updateItem: (id: string, data: UpdateT) => Promise<T | null>
  deleteItem: (id: string) => Promise<boolean>
  
  // 对话框状态
  dialogOpen: boolean
  setDialogOpen: (open: boolean) => void
  editingItem: T | null
  setEditingItem: (item: T | null) => void
  
  // 删除确认
  deleteDialogOpen: boolean
  setDeleteDialogOpen: (open: boolean) => void
  deletingId: string | null
  setDeletingId: (id: string | null) => void
  
  // 工具函数
  handleEdit: (item: T) => void
  handleCreate: () => void
  handleDelete: (id: string) => void
  handleSave: (data: CreateT | UpdateT) => Promise<void>
  handleDeleteConfirm: () => Promise<void>
}

/**
 * 通用 CRUD Hook
 */
export function useCrud<T extends { id?: string | number }, CreateT, UpdateT>(
  config: UseCrudConfig<T, CreateT, UpdateT>
): UseCrudReturn<T, CreateT, UpdateT> {
  const { toast } = useToast()
  
  // 数据状态
  const [items, setItems] = useState<T[]>([])
  const [item, setItem] = useState<T | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  
  // 分页状态
  const [pagination, setPaginationState] = useState<PaginationInfo>({
    page: config.initialPagination?.page || 1,
    pageSize: config.initialPagination?.pageSize || 20,
    total: 0,
    totalPages: 0
  })
  
  // 搜索和过滤状态
  const [filters, setFiltersState] = useState<SearchFilters>(
    config.initialFilters || {}
  )
  
  // 对话框状态
  const [dialogOpen, setDialogOpen] = useState(false)
  const [editingItem, setEditingItem] = useState<T | null>(null)
  
  // 删除确认状态
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [deletingId, setDeletingId] = useState<string | null>(null)
  
  // 获取 ID 的辅助函数
  const getId = useCallback((item: T): string => {
    if (item.id) {
      return String(item.id)
    }
    // 尝试其他常见 ID 字段
    const idFields = ["_id", "agent_id", "account_id", "script_id", "task_id"]
    for (const field of idFields) {
      if ((item as any)[field]) {
        return String((item as any)[field])
      }
    }
    throw new Error("无法获取项目 ID")
  }, [])
  
  // 设置分页
  const setPagination = useCallback((newPagination: Partial<PaginationInfo>) => {
    setPaginationState(prev => ({ ...prev, ...newPagination }))
  }, [])
  
  // 设置过滤
  const setFilters = useCallback((
    newFilters: SearchFilters | ((prev: SearchFilters) => SearchFilters)
  ) => {
    setFiltersState(prev => {
      const updated = typeof newFilters === "function" ? newFilters(prev) : newFilters
      return { ...prev, ...updated }
    })
  }, [])
  
  // 重置过滤
  const resetFilters = useCallback(() => {
    setFiltersState(config.initialFilters || {})
  }, [config.initialFilters])
  
  // 获取列表
  const fetchItems = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      
      const params = {
        ...filters,
        page: pagination.page,
        page_size: pagination.pageSize
      }
      
      const result = await config.listApi(params)
      
      // 处理不同的返回格式
      if (Array.isArray(result)) {
        setItems(result)
        setPagination(prev => ({
          ...prev,
          total: result.length,
          totalPages: Math.ceil(result.length / prev.pageSize)
        }))
      } else {
        setItems(result.items || [])
        setPagination(prev => ({
          ...prev,
          total: result.total || result.items?.length || 0,
          totalPages: result.total 
            ? Math.ceil(result.total / prev.pageSize)
            : Math.ceil((result.items?.length || 0) / prev.pageSize)
        }))
      }
    } catch (err) {
      const error = err instanceof Error ? err : new Error(String(err))
      setError(error.message)
      console.error("[useCrud] 获取列表失败:", error)
      toast({
        title: "获取数据失败",
        description: error.message,
        variant: "destructive"
      })
    } finally {
      setLoading(false)
    }
  }, [filters, pagination.page, pagination.pageSize, config.listApi, toast, setPagination])
  
  // 获取单个项目
  const getItem = useCallback(async (id: string): Promise<T | null> => {
    if (!config.getApi) {
      // 从列表中查找
      const found = items.find(item => getId(item) === id)
      return found || null
    }
    
    try {
      setLoading(true)
      setError(null)
      const data = await config.getApi(id)
      setItem(data)
      return data
    } catch (err) {
      const error = err instanceof Error ? err : new Error(String(err))
      setError(error.message)
      console.error("[useCrud] 获取项目失败:", error)
      toast({
        title: "获取数据失败",
        description: error.message,
        variant: "destructive"
      })
      return null
    } finally {
      setLoading(false)
    }
  }, [config.getApi, items, getId, toast])
  
  // 创建项目
  const createItem = useCallback(async (data: CreateT): Promise<T | null> => {
    try {
      setLoading(true)
      setError(null)
      const newItem = await config.createApi(data)
      
      // 添加到列表
      setItems(prev => [newItem, ...prev])
      
      // 触发成功回调
      if (config.onSuccess) {
        config.onSuccess("create", newItem)
      }
      
      toast({
        title: "创建成功",
        description: "项目已成功创建"
      })
      
      return newItem
    } catch (err) {
      const error = err instanceof Error ? err : new Error(String(err))
      setError(error.message)
      console.error("[useCrud] 创建失败:", error)
      
      if (config.onError) {
        config.onError(error, "create")
      }
      
      toast({
        title: "创建失败",
        description: error.message,
        variant: "destructive"
      })
      return null
    } finally {
      setLoading(false)
    }
  }, [config, toast])
  
  // 更新项目
  const updateItem = useCallback(async (id: string, data: UpdateT): Promise<T | null> => {
    try {
      setLoading(true)
      setError(null)
      const updatedItem = await config.updateApi(id, data)
      
      // 更新列表中的项目
      setItems(prev => prev.map(item => getId(item) === id ? updatedItem : item))
      
      // 如果当前查看的就是这个项目，也更新
      if (item && getId(item) === id) {
        setItem(updatedItem)
      }
      
      // 触发成功回调
      if (config.onSuccess) {
        config.onSuccess("update", updatedItem)
      }
      
      toast({
        title: "更新成功",
        description: "项目已成功更新"
      })
      
      return updatedItem
    } catch (err) {
      const error = err instanceof Error ? err : new Error(String(err))
      setError(error.message)
      console.error("[useCrud] 更新失败:", error)
      
      if (config.onError) {
        config.onError(error, "update")
      }
      
      toast({
        title: "更新失败",
        description: error.message,
        variant: "destructive"
      })
      return null
    } finally {
      setLoading(false)
    }
  }, [config, item, getId, toast])
  
  // 删除项目
  const deleteItem = useCallback(async (id: string): Promise<boolean> => {
    try {
      setLoading(true)
      setError(null)
      await config.deleteApi(id)
      
      // 从列表中移除
      setItems(prev => prev.filter(item => getId(item) !== id))
      
      // 如果当前查看的就是这个项目，清空
      if (item && getId(item) === id) {
        setItem(null)
      }
      
      // 触发成功回调
      if (config.onSuccess) {
        config.onSuccess("delete")
      }
      
      toast({
        title: "删除成功",
        description: "项目已成功删除"
      })
      
      return true
    } catch (err) {
      const error = err instanceof Error ? err : new Error(String(err))
      setError(error.message)
      console.error("[useCrud] 删除失败:", error)
      
      if (config.onError) {
        config.onError(error, "delete")
      }
      
      toast({
        title: "删除失败",
        description: error.message,
        variant: "destructive"
      })
      return false
    } finally {
      setLoading(false)
    }
  }, [config, item, getId, toast])
  
  // 处理编辑
  const handleEdit = useCallback((item: T) => {
    setEditingItem(item)
    setDialogOpen(true)
  }, [])
  
  // 处理创建
  const handleCreate = useCallback(() => {
    setEditingItem(null)
    setDialogOpen(true)
  }, [])
  
  // 处理删除
  const handleDelete = useCallback((id: string) => {
    setDeletingId(id)
    setDeleteDialogOpen(true)
  }, [])
  
  // 处理保存（创建或更新）
  const handleSave = useCallback(async (data: CreateT | UpdateT) => {
    if (editingItem) {
      // 更新
      const id = getId(editingItem)
      await updateItem(id, data as UpdateT)
    } else {
      // 创建
      await createItem(data as CreateT)
    }
    setDialogOpen(false)
    setEditingItem(null)
  }, [editingItem, getId, updateItem, createItem])
  
  // 处理删除确认
  const handleDeleteConfirm = useCallback(async () => {
    if (deletingId) {
      await deleteItem(deletingId)
      setDeleteDialogOpen(false)
      setDeletingId(null)
    }
  }, [deletingId, deleteItem])
  
  // 自动获取列表
  useEffect(() => {
    if (config.autoFetch !== false) {
      fetchItems()
    }
  }, [pagination.page, pagination.pageSize, filters, config.autoFetch]) // fetchItems 依赖项已包含
  
  return {
    items,
    item,
    loading,
    error,
    pagination,
    setPagination,
    filters,
    setFilters,
    resetFilters,
    fetchItems,
    getItem,
    createItem,
    updateItem,
    deleteItem,
    dialogOpen,
    setDialogOpen,
    editingItem,
    setEditingItem,
    deleteDialogOpen,
    setDeleteDialogOpen,
    deletingId,
    setDeletingId,
    handleEdit,
    handleCreate,
    handleDelete,
    handleSave,
    handleDeleteConfirm
  }
}

/**
 * 通用数据表格组件
 * 支持搜索、过滤、分页、批量操作
 */

"use client"

import * as React from "react"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import { Search, X, ChevronLeft, ChevronRight, ChevronsLeft, ChevronsRight } from "lucide-react"
import { cn } from "@/lib/utils"

// 列定义
export interface Column<T> {
  key: string
  header: string | React.ReactNode
  accessor?: (item: T) => React.ReactNode
  sortable?: boolean
  width?: string
  className?: string
}

// DataTable Props
export interface DataTableProps<T> {
  data: T[]
  columns: Column<T>[]
  loading?: boolean
  error?: string | null
  
  // 搜索和过滤
  searchable?: boolean
  searchPlaceholder?: string
  searchValue?: string
  onSearchChange?: (value: string) => void
  
  filterable?: boolean
  filters?: React.ReactNode
  
  // 分页
  pagination?: {
    page: number
    pageSize: number
    total: number
    totalPages: number
  }
  onPaginationChange?: (page: number, pageSize: number) => void
  pageSizeOptions?: number[]
  
  // 操作
  onEdit?: (item: T) => void
  onDelete?: (item: T) => void
  onRowClick?: (item: T) => void
  actions?: (item: T) => React.ReactNode
  
  // 批量操作
  batchActions?: React.ReactNode
  selectable?: boolean
  selectedItems?: T[]
  onSelectionChange?: (items: T[]) => void
  getItemId?: (item: T) => string | number
  
  // 空状态
  emptyMessage?: string
  emptyDescription?: string
  
  // 样式
  className?: string
  rowClassName?: (item: T) => string
}

/**
 * 通用数据表格组件
 */
export function DataTable<T>({
  data,
  columns,
  loading = false,
  error = null,
  searchable = true,
  searchPlaceholder = "搜索...",
  searchValue,
  onSearchChange,
  filterable = false,
  filters,
  pagination,
  onPaginationChange,
  pageSizeOptions = [10, 20, 50, 100],
  onEdit,
  onDelete,
  onRowClick,
  actions,
  batchActions,
  selectable = false,
  selectedItems = [],
  onSelectionChange,
  getItemId,
  emptyMessage = "暂无数据",
  emptyDescription,
  className,
  rowClassName
}: DataTableProps<T>) {
  const [internalSearch, setInternalSearch] = React.useState("")
  const searchValueToUse = searchValue !== undefined ? searchValue : internalSearch
  const setSearchValue = onSearchChange || setInternalSearch
  
  // 获取项目 ID
  const getId = React.useCallback((item: T): string | number => {
    if (getItemId) {
      return getItemId(item)
    }
    // 尝试常见 ID 字段
    const itemAny = item as any
    return itemAny.id || itemAny._id || itemAny.agent_id || itemAny.account_id || String(item)
  }, [getItemId])
  
  // 选择处理
  const isSelected = React.useCallback((item: T) => {
    if (!selectable || !selectedItems) return false
    const id = getId(item)
    return selectedItems.some(selected => getId(selected) === id)
  }, [selectable, selectedItems, getId])
  
  const toggleSelect = React.useCallback((item: T) => {
    if (!selectable || !onSelectionChange) return
    
    const id = getId(item)
    const isCurrentlySelected = selectedItems.some(selected => getId(selected) === id)
    
    if (isCurrentlySelected) {
      onSelectionChange(selectedItems.filter(selected => getId(selected) !== id))
    } else {
      onSelectionChange([...selectedItems, item])
    }
  }, [selectable, onSelectionChange, selectedItems, getId])
  
  const toggleSelectAll = React.useCallback(() => {
    if (!selectable || !onSelectionChange) return
    
    if (selectedItems.length === data.length) {
      onSelectionChange([])
    } else {
      onSelectionChange([...data])
    }
  }, [selectable, onSelectionChange, selectedItems, data])
  
  // 分页处理
  const handlePageChange = React.useCallback((newPage: number) => {
    if (onPaginationChange && pagination) {
      onPaginationChange(newPage, pagination.pageSize)
    }
  }, [onPaginationChange, pagination])
  
  const handlePageSizeChange = React.useCallback((newPageSize: string) => {
    if (onPaginationChange && pagination) {
      onPaginationChange(1, parseInt(newPageSize))
    }
  }, [onPaginationChange, pagination])
  
  return (
    <div className={cn("space-y-4", className)}>
      {/* 搜索和过滤工具栏 */}
      {(searchable || filterable || batchActions) && (
        <div className="flex items-center justify-between gap-4">
          <div className="flex items-center gap-2 flex-1">
            {searchable && (
              <div className="relative flex-1 max-w-sm">
                <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder={searchPlaceholder}
                  value={searchValueToUse}
                  onChange={(e) => setSearchValue(e.target.value)}
                  className="pl-8"
                />
                {searchValueToUse && (
                  <Button
                    variant="ghost"
                    size="icon"
                    className="absolute right-0 top-0 h-full"
                    onClick={() => setSearchValue("")}
                  >
                    <X className="h-4 w-4" />
                  </Button>
                )}
              </div>
            )}
            {filterable && filters}
          </div>
          {batchActions && selectedItems.length > 0 && (
            <div className="flex items-center gap-2">
              <Badge variant="secondary">
                已选择 {selectedItems.length} 项
              </Badge>
              {batchActions}
            </div>
          )}
        </div>
      )}
      
      {/* 表格 */}
      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              {selectable && (
                <TableHead className="w-12">
                  <input
                    type="checkbox"
                    checked={data.length > 0 && selectedItems.length === data.length}
                    onChange={toggleSelectAll}
                    className="rounded border-gray-300"
                  />
                </TableHead>
              )}
              {columns.map((column) => (
                <TableHead
                  key={column.key}
                  style={{ width: column.width }}
                  className={column.className}
                >
                  {column.header}
                </TableHead>
              ))}
              {(onEdit || onDelete || actions) && (
                <TableHead className="w-24 text-right">操作</TableHead>
              )}
            </TableRow>
          </TableHeader>
          <TableBody>
            {loading ? (
              // 加载状态
              Array.from({ length: pagination?.pageSize || 5 }).map((_, index) => (
                <TableRow key={index}>
                  {selectable && (
                    <TableCell>
                      <Skeleton className="h-4 w-4" />
                    </TableCell>
                  )}
                  {columns.map((column) => (
                    <TableCell key={column.key}>
                      <Skeleton className="h-4 w-full" />
                    </TableCell>
                  ))}
                  {(onEdit || onDelete || actions) && (
                    <TableCell>
                      <Skeleton className="h-4 w-16" />
                    </TableCell>
                  )}
                </TableRow>
              ))
            ) : error ? (
              // 错误状态
              <TableRow>
                <TableCell
                  colSpan={columns.length + (selectable ? 1 : 0) + ((onEdit || onDelete || actions) ? 1 : 0)}
                  className="text-center text-destructive py-8"
                >
                  {error}
                </TableCell>
              </TableRow>
            ) : data.length === 0 ? (
              // 空状态
              <TableRow>
                <TableCell
                  colSpan={columns.length + (selectable ? 1 : 0) + ((onEdit || onDelete || actions) ? 1 : 0)}
                  className="text-center py-8 text-muted-foreground"
                >
                  <div className="flex flex-col items-center gap-2">
                    <p className="font-medium">{emptyMessage}</p>
                    {emptyDescription && (
                      <p className="text-sm">{emptyDescription}</p>
                    )}
                  </div>
                </TableCell>
              </TableRow>
            ) : (
              // 数据行
              data.map((item, index) => (
                <TableRow
                  key={String(getId(item))}
                  className={cn(
                    onRowClick && "cursor-pointer",
                    rowClassName && rowClassName(item)
                  )}
                  onClick={() => onRowClick?.(item)}
                >
                  {selectable && (
                    <TableCell>
                      <input
                        type="checkbox"
                        checked={isSelected(item)}
                        onChange={() => toggleSelect(item)}
                        onClick={(e) => e.stopPropagation()}
                        className="rounded border-gray-300"
                      />
                    </TableCell>
                  )}
                  {columns.map((column) => (
                    <TableCell key={column.key} className={column.className}>
                      {column.accessor ? column.accessor(item) : (item as any)[column.key]}
                    </TableCell>
                  ))}
                  {(onEdit || onDelete || actions) && (
                    <TableCell className="text-right" onClick={(e) => e.stopPropagation()}>
                      <div className="flex items-center justify-end gap-2">
                        {actions && actions(item)}
                        {onEdit && (
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => onEdit(item)}
                          >
                            <span className="sr-only">编辑</span>
                            编辑
                          </Button>
                        )}
                        {onDelete && (
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => onDelete(item)}
                          >
                            <span className="sr-only">删除</span>
                            删除
                          </Button>
                        )}
                      </div>
                    </TableCell>
                  )}
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>
      
      {/* 分页 */}
      {pagination && onPaginationChange && (
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-sm text-muted-foreground">
              共 {pagination.total} 条，第 {pagination.page} / {pagination.totalPages} 页
            </span>
            <Select
              value={String(pagination.pageSize)}
              onValueChange={handlePageSizeChange}
            >
              <SelectTrigger className="w-20">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {pageSizeOptions.map((size) => (
                  <SelectItem key={size} value={String(size)}>
                    {size} 条/页
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="icon"
              onClick={() => handlePageChange(1)}
              disabled={pagination.page === 1}
            >
              <ChevronsLeft className="h-4 w-4" />
            </Button>
            <Button
              variant="outline"
              size="icon"
              onClick={() => handlePageChange(pagination.page - 1)}
              disabled={pagination.page === 1}
            >
              <ChevronLeft className="h-4 w-4" />
            </Button>
            <span className="text-sm">
              {pagination.page} / {pagination.totalPages}
            </span>
            <Button
              variant="outline"
              size="icon"
              onClick={() => handlePageChange(pagination.page + 1)}
              disabled={pagination.page >= pagination.totalPages}
            >
              <ChevronRight className="h-4 w-4" />
            </Button>
            <Button
              variant="outline"
              size="icon"
              onClick={() => handlePageChange(pagination.totalPages)}
              disabled={pagination.page >= pagination.totalPages}
            >
              <ChevronsRight className="h-4 w-4" />
            </Button>
          </div>
        </div>
      )}
    </div>
  )
}

"use client"

import { useState } from "react"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Label } from "@/components/ui/label"
import { Search, X, Filter } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible"

export interface SearchFilters {
  search?: string
  status?: string
  script_id?: string
  server_id?: string
  active?: boolean
  mode?: string
  sort_by?: string
  sort_order?: "asc" | "desc"
}

interface AdvancedSearchProps {
  onSearch: (filters: SearchFilters) => void
  onReset: () => void
  filters: SearchFilters
  searchPlaceholder?: string
  showStatusFilter?: boolean
  showScriptFilter?: boolean
  showServerFilter?: boolean
  showActiveFilter?: boolean
  showModeFilter?: boolean
  statusOptions?: Array<{ value: string; label: string }>
  scriptOptions?: Array<{ value: string; label: string }>
  serverOptions?: Array<{ value: string; label: string }>
  sortOptions?: Array<{ value: string; label: string }>
}

export function AdvancedSearch({
  onSearch,
  onReset,
  filters,
  searchPlaceholder = "搜索...",
  showStatusFilter = false,
  showScriptFilter = false,
  showServerFilter = false,
  showActiveFilter = false,
  showModeFilter = false,
  statusOptions = [],
  scriptOptions = [],
  serverOptions = [],
  sortOptions = [
    { value: "created_at", label: "創建時間" },
    { value: "updated_at", label: "更新時間" },
    { value: "name", label: "名稱" },
  ],
}: AdvancedSearchProps) {
  const [localFilters, setLocalFilters] = useState<SearchFilters>(filters)
  const [isOpen, setIsOpen] = useState(false)

  const handleSearch = () => {
    onSearch(localFilters)
  }

  const handleReset = () => {
    setLocalFilters({})
    onReset()
  }

  const hasActiveFilters = () => {
    return !!(
      localFilters.search ||
      localFilters.status ||
      localFilters.script_id ||
      localFilters.server_id ||
      localFilters.active !== undefined ||
      localFilters.mode ||
      localFilters.sort_by ||
      localFilters.sort_order
    )
  }

  return (
    <Card className="mb-4">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-base">搜索和過濾</CardTitle>
          <Collapsible open={isOpen} onOpenChange={setIsOpen}>
            <CollapsibleTrigger asChild>
              <Button variant="ghost" size="sm">
                <Filter className="h-4 w-4 mr-2" />
                {isOpen ? "收起" : "展開"}
              </Button>
            </CollapsibleTrigger>
          </Collapsible>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {/* 搜索框 */}
          <div className="flex gap-2">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder={searchPlaceholder}
                value={localFilters.search || ""}
                onChange={(e) =>
                  setLocalFilters({ ...localFilters, search: e.target.value })
                }
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    handleSearch()
                  }
                }}
                className="pl-10"
              />
            </div>
            <Button onClick={handleSearch}>
              <Search className="h-4 w-4 mr-2" />
              搜索
            </Button>
            {hasActiveFilters() && (
              <Button variant="outline" onClick={handleReset}>
                <X className="h-4 w-4 mr-2" />
                重置
              </Button>
            )}
          </div>

          {/* 高級過濾選項 */}
          <Collapsible open={isOpen} onOpenChange={setIsOpen}>
            <CollapsibleContent>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 pt-2 border-t">
                {/* 狀態過濾 */}
                {showStatusFilter && (
                  <div>
                    <Label>狀態</Label>
                    <Select
                      value={localFilters.status || "__all__"}
                      onValueChange={(value) =>
                        setLocalFilters({
                          ...localFilters,
                          status: value === "__all__" ? undefined : value,
                        })
                      }
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="全部狀態" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="__all__">全部狀態</SelectItem>
                        {statusOptions.map((option) => (
                          <SelectItem key={option.value} value={option.value}>
                            {option.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                )}

                {/* 劇本過濾 */}
                {showScriptFilter && (
                  <div>
                    <Label>劇本</Label>
                    <Select
                      value={localFilters.script_id || "__all__"}
                      onValueChange={(value) =>
                        setLocalFilters({
                          ...localFilters,
                          script_id: value === "__all__" ? undefined : value,
                        })
                      }
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="全部劇本" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="__all__">全部劇本</SelectItem>
                        {scriptOptions.map((option) => (
                          <SelectItem key={option.value} value={option.value}>
                            {option.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                )}

                {/* 服務器過濾 */}
                {showServerFilter && (
                  <div>
                    <Label>服務器</Label>
                    <Select
                      value={localFilters.server_id || "__all__"}
                      onValueChange={(value) =>
                        setLocalFilters({
                          ...localFilters,
                          server_id: value === "__all__" ? undefined : value,
                        })
                      }
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="全部服務器" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="__all__">全部服務器</SelectItem>
                        {serverOptions.map((option) => (
                          <SelectItem key={option.value} value={option.value}>
                            {option.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                )}

                {/* 激活狀態過濾 */}
                {showActiveFilter && (
                  <div>
                    <Label>激活狀態</Label>
                    <Select
                      value={
                        localFilters.active === undefined
                          ? "__all__"
                          : localFilters.active
                          ? "true"
                          : "false"
                      }
                      onValueChange={(value) =>
                        setLocalFilters({
                          ...localFilters,
                          active: value === "__all__" ? undefined : value === "true",
                        })
                      }
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="全部" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="__all__">全部</SelectItem>
                        <SelectItem value="true">已激活</SelectItem>
                        <SelectItem value="false">未激活</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                )}

                {/* 分配模式過濾 */}
                {showModeFilter && (
                  <div>
                    <Label>分配模式</Label>
                    <Select
                      value={localFilters.mode || "__all__"}
                      onValueChange={(value) =>
                        setLocalFilters({
                          ...localFilters,
                          mode: value === "__all__" ? undefined : value,
                        })
                      }
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="全部模式" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="__all__">全部模式</SelectItem>
                        <SelectItem value="auto">自動</SelectItem>
                        <SelectItem value="manual">手動</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                )}

                {/* 排序字段 */}
                <div>
                  <Label>排序字段</Label>
                  <Select
                    value={localFilters.sort_by || "created_at"}
                    onValueChange={(value) =>
                      setLocalFilters({
                        ...localFilters,
                        sort_by: value,
                      })
                    }
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {sortOptions.map((option) => (
                        <SelectItem key={option.value} value={option.value}>
                          {option.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                {/* 排序順序 */}
                <div>
                  <Label>排序順序</Label>
                  <Select
                    value={localFilters.sort_order || "desc"}
                    onValueChange={(value: "asc" | "desc") =>
                      setLocalFilters({
                        ...localFilters,
                        sort_order: value,
                      })
                    }
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="desc">降序</SelectItem>
                      <SelectItem value="asc">升序</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </CollapsibleContent>
          </Collapsible>
        </div>
      </CardContent>
    </Card>
  )
}


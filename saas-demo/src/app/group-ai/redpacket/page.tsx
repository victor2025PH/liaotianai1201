/**
 * 红包策略管理页面 - Phase 2: 拟人化版
 * 使用通用基础设施重构
 */

"use client"

import { useCrud } from "@/hooks/useCrud"
import { DataTable, Column, CrudDialog, FormField } from "@/components/common"
import {
  getStrategies,
  createStrategy,
  updateStrategy,
  deleteStrategy,
  syncStrategies,
  type RedPacketStrategy,
  type RedPacketStrategyCreate,
  type RedPacketStrategyUpdate
} from "@/lib/api/strategies"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { InputTags } from "@/components/ui/input-tags"
import { Slider } from "@/components/ui/slider"
import { Switch } from "@/components/ui/switch"
import { 
  Gift, 
  RefreshCw, 
  Plus,
  Clock,
  Target,
  Percent
} from "lucide-react"
import { useToast } from "@/hooks/use-toast"
import { useState } from "react"

// 定义列结构
const columns: Column<RedPacketStrategy>[] = [
  {
    key: "name",
    header: "策略名称",
    accessor: (item) => (
      <div className="font-medium">{item.name}</div>
    )
  },
  {
    key: "keywords",
    header: "关键词",
    accessor: (item) => (
      <div className="flex flex-wrap gap-1">
        {item.keywords.slice(0, 3).map((keyword, idx) => (
          <Badge key={idx} variant="secondary" className="text-xs">
            {keyword}
          </Badge>
        ))}
        {item.keywords.length > 3 && (
          <Badge variant="outline" className="text-xs">
            +{item.keywords.length - 3}
          </Badge>
        )}
      </div>
    )
  },
  {
    key: "delay",
    header: "延迟范围",
    accessor: (item) => (
      <div className="flex items-center gap-1 text-sm">
        <Clock className="h-3 w-3 text-muted-foreground" />
        <span>
          {item.delay_min}ms - {item.delay_max}ms
        </span>
      </div>
    )
  },
  {
    key: "target_groups",
    header: "目标群组",
    accessor: (item) => (
      <div className="flex items-center gap-1 text-sm">
        <Target className="h-3 w-3 text-muted-foreground" />
        <span>
          {item.target_groups.length > 0 
            ? `${item.target_groups.length} 个群组`
            : "所有群组"
          }
        </span>
      </div>
    )
  },
  {
    key: "probability",
    header: "抢包概率",
    accessor: (item) => (
      <div className="flex items-center gap-1 text-sm">
        <Percent className="h-3 w-3 text-muted-foreground" />
        <span>{item.probability || 100}%</span>
      </div>
    )
  },
  {
    key: "enabled",
    header: "状态",
    accessor: (item) => (
      <Badge variant={item.enabled ? "default" : "secondary"}>
        {item.enabled ? "启用" : "禁用"}
      </Badge>
    )
  }
]

export default function RedPacketPage() {
  const { toast } = useToast()
  const [syncing, setSyncing] = useState(false)
  
  // 使用 useCrud Hook 管理策略列表
  const crud = useCrud<RedPacketStrategy, RedPacketStrategyCreate, RedPacketStrategyUpdate>({
    listApi: getStrategies,
    getApi: async (id) => {
      const { getStrategy } = await import("@/lib/api/strategies")
      return getStrategy(id)
    },
    createApi: createStrategy,
    updateApi: (id, data) => updateStrategy(id, data),
    deleteApi: deleteStrategy,
    initialPagination: {
      page: 1,
      pageSize: 20
    },
    autoFetch: true
  })
  
  // 处理立即同步
  const handleSync = async () => {
    try {
      setSyncing(true)
      await syncStrategies()
      // 刷新列表以确保数据最新
      await crud.fetchItems()
      toast({
        title: "同步成功",
        description: "策略已同步到所有在线 Agent"
      })
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : String(error)
      toast({
        title: "同步失败",
        description: errorMessage,
        variant: "destructive"
      })
    } finally {
      setSyncing(false)
    }
  }
  
  // 定义表单字段
  const formFields: FormField[] = [
    {
      name: "name",
      label: "策略名称",
      type: "text",
      required: true,
      placeholder: "例如：USDT 红包策略"
    },
    {
      name: "description",
      label: "描述",
      type: "textarea",
      placeholder: "策略描述（可选）"
    },
    {
      name: "keywords",
      label: "关键词",
      required: true,
      render: (value: string[] = [], onChange) => (
        <InputTags
          value={value}
          onChange={onChange}
          placeholder="输入关键词后按回车添加（如：USDT, TON, 积分）"
        />
      ),
      validation: (value) => {
        if (!value || (Array.isArray(value) && value.length === 0)) {
          return "至少需要添加一个关键词"
        }
        return null
      }
    },
    {
      name: "delay_min",
      label: "最小延迟（毫秒）",
      type: "number",
      required: true,
      placeholder: "1000",
      validation: (value) => {
        if (value === undefined || value === null || value === "") {
          return "最小延迟不能为空"
        }
        const num = Number(value)
        if (isNaN(num) || num < 0) {
          return "最小延迟必须大于等于 0"
        }
        return null
      }
    },
    {
      name: "delay_max",
      label: "最大延迟（毫秒）",
      type: "number",
      required: true,
      placeholder: "5000",
      validation: (value) => {
        if (value === undefined || value === null || value === "") {
          return "最大延迟不能为空"
        }
        const num = Number(value)
        if (isNaN(num) || num < 0) {
          return "最大延迟必须大于等于 0"
        }
        // 检查是否大于等于最小延迟（需要在表单验证时获取 delay_min 的值）
        return null
      }
    },
    {
      name: "target_groups",
      label: "目标群组 ID",
      type: "textarea",
      placeholder: "输入群组 ID，用逗号分隔（留空表示所有群组）",
      render: (value: number[] = [], onChange) => {
        const textValue = Array.isArray(value) ? value.join(", ") : ""
        return (
          <textarea
            value={textValue}
            onChange={(e) => {
              const text = e.target.value.trim()
              if (!text) {
                onChange([])
                return
              }
              // 解析逗号分隔的数字
              const groups = text
                .split(",")
                .map(s => s.trim())
                .filter(s => s)
                .map(s => {
                  const num = parseInt(s, 10)
                  return isNaN(num) ? null : num
                })
                .filter((num): num is number => num !== null)
              onChange(groups)
            }}
            placeholder="例如：-1001234567890, -1009876543210"
            className="flex min-h-[80px] w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
          />
        )
      }
    },
    {
      name: "probability",
      label: "抢包概率",
      render: (value: number = 100, onChange) => (
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-sm text-muted-foreground">概率: {value}%</span>
            <input
              type="number"
              min="0"
              max="100"
              value={value}
              onChange={(e) => {
                const num = parseInt(e.target.value, 10)
                if (!isNaN(num) && num >= 0 && num <= 100) {
                  onChange(num)
                }
              }}
              className="w-20 h-9 rounded-md border border-input bg-transparent px-2 text-sm"
            />
          </div>
          <Slider
            value={[value]}
            onValueChange={([val]) => onChange(val)}
            min={0}
            max={100}
            step={1}
            className="w-full"
          />
          <p className="text-xs text-muted-foreground">
            设置抢包概率，模拟偶尔没看到红包的情况（100% = 总是抢包）
          </p>
        </div>
      )
    },
    {
      name: "enabled",
      label: "启用策略",
      type: "checkbox",
      render: (value: boolean = true, onChange) => (
        <div className="flex items-center space-x-2">
          <Switch
            checked={value}
            onCheckedChange={onChange}
          />
          <span className="text-sm text-muted-foreground">
            {value ? "策略已启用" : "策略已禁用"}
          </span>
        </div>
      )
    }
  ]
  
  // 处理保存（需要特殊处理 target_groups 和 keywords）
  const handleSave = async (data: RedPacketStrategyCreate | RedPacketStrategyUpdate) => {
    // 确保 keywords 是数组
    const processedData = {
      ...data,
      keywords: Array.isArray(data.keywords) ? data.keywords : [],
      target_groups: Array.isArray(data.target_groups) ? data.target_groups : []
    }
    
    // 验证 delay_max >= delay_min
    if (processedData.delay_min !== undefined && processedData.delay_max !== undefined) {
      if (processedData.delay_max < processedData.delay_min) {
        toast({
          title: "验证失败",
          description: "最大延迟必须大于等于最小延迟",
          variant: "destructive"
        })
        return
      }
    }
    
    await crud.handleSave(processedData)
  }
  
  return (
    <div className="container mx-auto py-6 space-y-4">
      {/* 标题和操作栏 */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Gift className="h-6 w-6" />
            红包策略管理
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            配置拟人化抢包策略，支持 USDT、TON、积分等多种红包类型
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            onClick={handleSync}
            variant="outline"
            size="sm"
            disabled={syncing}
          >
            <RefreshCw className={`mr-2 h-4 w-4 ${syncing ? 'animate-spin' : ''}`} />
            立即同步
          </Button>
          <Button
            onClick={crud.handleCreate}
            size="sm"
          >
            <Plus className="mr-2 h-4 w-4" />
            创建策略
          </Button>
        </div>
      </div>
      
      {/* 数据表格 */}
      <DataTable
        data={crud.items}
        columns={columns}
        loading={crud.loading}
        error={crud.error}
        pagination={crud.pagination}
        onPaginationChange={(page, pageSize) => {
          crud.setPagination({ page, pageSize })
        }}
        onEdit={crud.handleEdit}
        onDelete={(item) => {
          // DataTable 传递的是 item 对象，但 handleDelete 需要 id
          const itemId = item.id
          if (itemId !== undefined && itemId !== null) {
            crud.handleDelete(String(itemId))
          }
        }}
        searchable
        searchPlaceholder="搜索策略名称或关键词..."
        searchValue={crud.filters.search}
        onSearchChange={(value) => crud.setFilters({ search: value })}
        getItemId={(item) => item.id}
        emptyMessage="暂无策略"
        emptyDescription="创建第一个红包策略，开始使用拟人化抢包功能。"
      />
      
      {/* 删除确认对话框 */}
      <AlertDialog 
        open={crud.deleteDialogOpen} 
        onOpenChange={crud.setDeleteDialogOpen}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>确认删除</AlertDialogTitle>
            <AlertDialogDescription>
              确定要删除策略 <strong>{crud.items.find(item => item.id === crud.deletingId)?.name}</strong> 吗？
              此操作无法撤销。
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel
              onClick={() => {
                crud.setDeleteDialogOpen(false)
                crud.setDeletingId(null)
              }}
            >
              取消
            </AlertDialogCancel>
            <AlertDialogAction
              onClick={crud.handleDeleteConfirm}
              disabled={crud.loading}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              {crud.loading ? "删除中..." : "确认删除"}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
      
      {/* 创建/编辑对话框 */}
      <CrudDialog
        open={crud.dialogOpen}
        onOpenChange={crud.setDialogOpen}
        mode={crud.editingItem ? "edit" : "create"}
        title={crud.editingItem ? "编辑策略" : "创建策略"}
        description={crud.editingItem ? "修改红包策略配置" : "创建新的红包抢包策略"}
        fields={formFields}
        initialData={crud.editingItem || {
          keywords: [],
          delay_min: 1000,
          delay_max: 5000,
          target_groups: [],
          probability: 100,
          enabled: true
        }}
        onSubmit={handleSave}
        loading={crud.loading}
      />
      
    </div>
  )
}

/**
 * 智能剧场管理页面 - Phase 3: 多账号协同表演
 * 使用通用基础设施重构
 */

"use client"

import { useCrud } from "@/hooks/useCrud"
import { DataTable, Column, CrudDialog, FormField } from "@/components/common"
import {
  getScenarios,
  createScenario,
  updateScenario,
  deleteScenario,
  type TheaterScenario,
  type TheaterScenarioCreate,
  type TheaterScenarioUpdate,
  type TimelineAction
} from "@/lib/api/theater"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { InputTags } from "@/components/ui/input-tags"
import { Switch } from "@/components/ui/switch"
import { Textarea } from "@/components/ui/textarea"
import { TimelineEditor } from "@/components/theater/TimelineEditor"
import { ExecutionDialog } from "@/components/theater/ExecutionDialog"
import { 
  Theater, 
  RefreshCw, 
  Plus,
  Play,
  Edit,
  Trash2,
  Users,
  Clock,
  FileText
} from "lucide-react"
import { useToast } from "@/hooks/use-toast"
import { useState } from "react"

// 格式化相对时间
function formatRelativeTime(date: Date): string {
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const seconds = Math.floor(diff / 1000)
  const minutes = Math.floor(seconds / 60)
  const hours = Math.floor(minutes / 60)
  const days = Math.floor(hours / 24)
  
  if (days > 0) {
    return `${days} 天前`
  } else if (hours > 0) {
    return `${hours} 小时前`
  } else if (minutes > 0) {
    return `${minutes} 分钟前`
  } else {
    return `${seconds} 秒前`
  }
}

// 定义列结构
const columns: Column<TheaterScenario>[] = [
  {
    key: "name",
    header: "剧本名称",
    accessor: (item) => (
      <div className="font-medium">{item.name}</div>
    )
  },
  {
    key: "roles",
    header: "角色",
    accessor: (item) => (
      <div className="flex flex-wrap gap-1">
        {item.roles.map((role, idx) => (
          <Badge key={idx} variant="secondary" className="text-xs">
            {role}
          </Badge>
        ))}
      </div>
    )
  },
  {
    key: "timeline",
    header: "动作数量",
    accessor: (item) => (
      <div className="flex items-center gap-1 text-sm">
        <FileText className="h-3 w-3 text-muted-foreground" />
        <span>{item.timeline.length} 个动作</span>
      </div>
    )
  },
  {
    key: "created_at",
    header: "创建时间",
    accessor: (item) => (
      <div className="flex items-center gap-1 text-sm text-muted-foreground">
        <Clock className="h-3 w-3" />
        <span>{formatRelativeTime(new Date(item.created_at))}</span>
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

export default function TheaterPage() {
  const { toast } = useToast()
  const [executionDialogOpen, setExecutionDialogOpen] = useState(false)
  const [selectedScenario, setSelectedScenario] = useState<TheaterScenario | null>(null)
  
  const crud = useCrud<TheaterScenario, TheaterScenarioCreate, TheaterScenarioUpdate>({
    listApi: getScenarios,
    createApi: createScenario,
    updateApi: updateScenario,
    deleteApi: deleteScenario,
    autoFetch: true
  })
  
  // 处理执行
  const handleExecute = (scenario: TheaterScenario) => {
    setSelectedScenario(scenario)
    setExecutionDialogOpen(true)
  }
  
  // 处理保存（包含角色和时间轴的验证）
  const handleSave = async (data: TheaterScenarioCreate | TheaterScenarioUpdate) => {
    const processedData: any = { ...data }
    
    // 确保 roles 是数组
    if (processedData.roles && typeof processedData.roles === "string") {
      // 如果是字符串，尝试解析（逗号分隔）
      processedData.roles = processedData.roles
        .split(",")
        .map((r: string) => r.trim())
        .filter((r: string) => r.length > 0)
    }
    
    // 验证时间轴中的角色都在 roles 列表中
    if (processedData.timeline && Array.isArray(processedData.timeline)) {
      const rolesInTimeline = new Set(
        processedData.timeline
          .map((action: TimelineAction) => action.role)
          .filter((role: string) => role)
      )
      const definedRoles = new Set(processedData.roles || [])
      
      const missingRoles = Array.from(rolesInTimeline).filter(
        role => !definedRoles.has(role)
      )
      
      if (missingRoles.length > 0) {
        toast({
          title: "验证失败",
          description: `时间轴中使用了未定义的角色: ${missingRoles.join(", ")}`,
          variant: "destructive"
        })
        return
      }
    }
    
    await crud.handleSave(processedData)
  }
  
  // 表单字段定义
  const formFields: FormField[] = [
    {
      name: "name",
      label: "剧本名称",
      type: "text",
      required: true,
      placeholder: "例如: 看多看空对话"
    },
    {
      name: "description",
      label: "描述",
      type: "textarea",
      placeholder: "剧本描述（可选）"
    },
    {
      name: "roles",
      label: "角色列表",
      required: true,
      render: (value, onChange) => (
        <InputTags
          value={value || []}
          onChange={onChange}
          placeholder="输入角色名称，按 Enter 添加"
        />
      ),
      validation: (value) => {
        if (!Array.isArray(value) || value.length === 0) {
          return "至少需要添加一个角色"
        }
        return null
      }
    },
    {
      name: "timeline",
      label: "时间轴",
      required: true,
      render: (value, onChange) => {
        // 1. 优先从 crud.editingItem 获取 roles（如果正在编辑）
        const currentRoles = crud.editingItem?.roles || []
        
        // 2. 如果 roles 为空，从 timeline actions 中提取已使用的角色
        let roles: string[] = []
        if (currentRoles.length > 0) {
          roles = currentRoles
        } else {
          // 获取所有非空角色，并去重
          const rawRoles = (value || []).map((action: TimelineAction) => action.role)
          const uniqueRoles = Array.from(new Set(rawRoles)).filter((r): r is string => !!r)
          roles = uniqueRoles
        }
        
        // 3. 显式 return 组件
        return (
          <TimelineEditor
            value={value || []}
            onChange={onChange}
            roles={roles}
          />
        )
      },
      validation: (value) => {
        if (!Array.isArray(value) || value.length === 0) {
          return "至少需要添加一个时间轴动作"
        }
        return null
      }
    },
    {
      name: "enabled",
      label: "启用剧本",
      type: "checkbox",
      render: (value, onChange) => (
        <div className="flex items-center space-x-2">
          <Switch
            checked={value || false}
            onCheckedChange={onChange}
          />
          <span className="text-sm text-muted-foreground">
            启用后可以执行此剧本
          </span>
        </div>
      )
    }
  ]
  
  return (
    <div className="container mx-auto py-6 space-y-4">
      {/* 标题和操作栏 */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Theater className="h-6 w-6" />
          <div>
            <h1 className="text-2xl font-bold">智能剧场</h1>
            <p className="text-sm text-muted-foreground">
              多账号协同表演管理
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => crud.fetchItems()}
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            刷新
          </Button>
          <Button
            size="sm"
            onClick={() => crud.setCreateDialogOpen(true)}
          >
            <Plus className="h-4 w-4 mr-2" />
            创建剧本
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
        onPaginationChange={crud.setPagination}
        searchPlaceholder="搜索剧本名称..."
        onSearch={crud.setSearchQuery}
        actions={(item) => (
          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => handleExecute(item)}
              disabled={!item.enabled}
              title={!item.enabled ? "剧本已禁用，无法执行" : "执行剧本"}
            >
              <Play className="h-4 w-4" />
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => crud.handleEdit(item)}
            >
              <Edit className="h-4 w-4" />
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => crud.handleDelete(item)}
            >
              <Trash2 className="h-4 w-4 text-destructive" />
            </Button>
          </div>
        )}
      />
      
      {/* 创建/编辑对话框 */}
      <CrudDialog
        open={crud.createDialogOpen || crud.editDialogOpen}
        onOpenChange={(open) => {
          if (!open) {
            crud.setCreateDialogOpen(false)
            crud.setEditDialogOpen(false)
          }
        }}
        mode={crud.editDialogOpen ? "edit" : "create"}
        title={crud.editDialogOpen ? "编辑剧本" : "创建剧本"}
        description={
          crud.editDialogOpen
            ? "修改剧本信息、角色和时间轴"
            : "创建一个新的剧场场景剧本"
        }
        fields={formFields}
        initialData={crud.editDialogOpen ? crud.item : undefined}
        onSubmit={handleSave}
        loading={crud.loading}
        maxWidth="2xl"
      />
      
      {/* 执行配置对话框 */}
      <ExecutionDialog
        open={executionDialogOpen}
        onOpenChange={setExecutionDialogOpen}
        scenario={selectedScenario}
        onSuccess={() => {
          crud.fetchItems()
        }}
      />
      
      {/* 删除确认对话框 */}
      {crud.deleteDialogOpen && crud.item && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div className="bg-background border rounded-lg p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-semibold mb-2">确认删除</h3>
            <p className="text-sm text-muted-foreground mb-4">
              确定要删除剧本 "{crud.item.name}" 吗？此操作不可恢复。
            </p>
            <div className="flex justify-end gap-2">
              <Button
                variant="outline"
                onClick={() => crud.setDeleteDialogOpen(false)}
              >
                取消
              </Button>
              <Button
                variant="destructive"
                onClick={async () => {
                  await crud.deleteItem(crud.item!.id)
                  crud.setDeleteDialogOpen(false)
                }}
              >
                删除
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

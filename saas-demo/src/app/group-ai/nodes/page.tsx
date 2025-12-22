/**
 * 节点管理页面 - 使用通用基础设施重构
 * 
 * 功能：
 * - 使用 useCrud Hook 管理 Agent 列表
 * - 使用 useAgentStatus 显示实时状态
 * - 使用 DataTable 组件渲染表格
 * - 使用 CrudDialog 进行删除确认
 */

"use client"

import { useCrud } from "@/hooks/useCrud"
import { useAgentStatus } from "@/hooks/useWebSocket"
import { DataTable, Column } from "@/components/common"
import { getAgents, deleteAgent } from "@/lib/api/agents"
import type { Agent } from "@/lib/api/agents"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { 
  Monitor, 
  RefreshCw, 
  Trash2,
  Wifi,
  WifiOff,
  Clock,
  Activity
} from "lucide-react"
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog"
// 格式化相对时间的辅助函数
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

// 状态单元格组件
function StatusCell({ agentId }: { agentId: string }) {
  const { isOnline } = useAgentStatus(agentId)
  
  return (
    <div className="flex items-center gap-2">
      {isOnline ? (
        <>
          <div className="h-2 w-2 rounded-full bg-green-500 animate-pulse" />
          <Badge variant="default" className="bg-green-500">
            在线
          </Badge>
        </>
      ) : (
        <>
          <div className="h-2 w-2 rounded-full bg-gray-400" />
          <Badge variant="secondary">
            离线
          </Badge>
        </>
      )}
    </div>
  )
}

// 延迟单元格组件
function LatencyCell({ item }: { item: Agent }) {
  const { agent } = useAgentStatus(item.agent_id)
  const latency = agent?.latency || item.latency
  
  if (!latency) {
    return <span className="text-muted-foreground text-sm">-</span>
  }
  
  const color = latency < 50 ? "text-green-600" : latency < 100 ? "text-yellow-600" : "text-red-600"
  
  return (
    <div className="flex items-center gap-1">
      <Activity className="h-3 w-3 text-muted-foreground" />
      <span className={`text-sm font-medium ${color}`}>
        {latency}ms
      </span>
    </div>
  )
}

// 心跳单元格组件
function HeartbeatCell({ item }: { item: Agent }) {
  const { agent } = useAgentStatus(item.agent_id)
  const lastHeartbeat = agent?.last_heartbeat || item.last_heartbeat
  
  if (!lastHeartbeat) {
    return <span className="text-muted-foreground text-sm">-</span>
  }
  
  try {
    const date = new Date(lastHeartbeat)
    const relative = formatRelativeTime(date)
    
    return (
      <div className="flex items-center gap-1">
        <Clock className="h-3 w-3 text-muted-foreground" />
        <span className="text-sm text-muted-foreground">
          {relative}
        </span>
      </div>
    )
  } catch {
    return <span className="text-muted-foreground text-sm">{lastHeartbeat}</span>
  }
}

// 定义列结构
const columns: Column<Agent>[] = [
  {
    key: "agent_id",
    header: "Agent ID",
    accessor: (item) => (
      <code className="text-sm bg-muted px-2 py-1 rounded">
        {item.agent_id.substring(0, 8)}...
      </code>
    )
  },
  {
    key: "ip_address",
    header: "IP 地址",
    accessor: (item) => {
      const ip = item.metadata?.hostname || item.metadata?.ip || "-"
      return <span className="text-sm">{ip}</span>
    }
  },
  {
    key: "status",
    header: "状态",
    accessor: (item) => <StatusCell agentId={item.agent_id} />
  },
  {
    key: "latency",
    header: "延迟",
    accessor: (item) => <LatencyCell item={item} />
  },
  {
    key: "last_heartbeat",
    header: "最后心跳",
    accessor: (item) => <HeartbeatCell item={item} />
  },
  {
    key: "connected_at",
    header: "连接时间",
    accessor: (item) => {
      if (!item.connected_at) {
        return <span className="text-muted-foreground text-sm">-</span>
      }
      
      try {
        const date = new Date(item.connected_at)
        return (
          <span className="text-sm text-muted-foreground">
            {date.toLocaleString("zh-CN")}
          </span>
        )
      } catch {
        return <span className="text-muted-foreground text-sm">{item.connected_at}</span>
      }
    }
  }
]

export default function NodesPage() {
  // 使用 useCrud Hook 管理 Agent 列表
  const crud = useCrud<Agent, never, never>({
    listApi: getAgents,
    // Agent 是自动注册的，不需要 create/update API
    createApi: async () => {
      throw new Error("Agent 是自动注册的，无法手动创建")
    },
    updateApi: async () => {
      throw new Error("Agent 不支持更新操作")
    },
    deleteApi: deleteAgent,
    initialPagination: {
      page: 1,
      pageSize: 20
    },
    autoFetch: true
  })
  
  // 获取全局 Agent 状态统计
  const { onlineCount, totalCount, isConnected } = useAgentStatus()
  
  // 处理删除确认
  const handleDeleteConfirm = async () => {
    if (crud.deletingId) {
      const success = await crud.deleteItem(crud.deletingId)
      if (success) {
        crud.setDeleteDialogOpen(false)
        crud.setDeletingId(null)
      }
    }
  }
  
  return (
    <div className="container mx-auto py-6 space-y-4">
      {/* 标题和操作栏 */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Monitor className="h-6 w-6" />
            节点管理
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            管理所有连接的 Agent 节点
            {isConnected && (
              <span className="ml-2">
                · 在线: <span className="text-green-600 font-medium">{onlineCount}</span> / 
                总计: <span className="font-medium">{totalCount}</span>
              </span>
            )}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button 
            onClick={crud.fetchItems} 
            variant="outline" 
            size="sm"
            disabled={crud.loading}
          >
            <RefreshCw className={`mr-2 h-4 w-4 ${crud.loading ? 'animate-spin' : ''}`} />
            刷新
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
        onDelete={(item) => {
          crud.setDeletingId(item.agent_id)
          crud.setDeleteDialogOpen(true)
        }}
        searchable
        searchPlaceholder="搜索 Agent ID..."
        searchValue={crud.filters.search}
        onSearchChange={(value) => crud.setFilters({ search: value })}
        getItemId={(item) => item.agent_id}
        emptyMessage="暂无节点"
        emptyDescription="当前没有连接的 Agent 节点。请确保 Agent 客户端正在运行并已连接到服务器。"
      />
      
      {/* 删除确认对话框 */}
      <AlertDialog 
        open={crud.deleteDialogOpen} 
        onOpenChange={crud.setDeleteDialogOpen}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>确认断开连接</AlertDialogTitle>
            <AlertDialogDescription>
              确定要断开 Agent <code className="bg-muted px-1 rounded">
                {crud.deletingId?.substring(0, 8)}...
              </code> 的连接吗？
              <br />
              <span className="text-muted-foreground text-xs mt-1 block">
                注意：Agent 断开连接后，如果客户端仍在运行，会自动重新连接。
              </span>
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
              onClick={handleDeleteConfirm}
              disabled={crud.loading}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              {crud.loading ? "断开中..." : "确认断开"}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  )
}

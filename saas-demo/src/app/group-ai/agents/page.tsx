/**
 * Agent 管理页面 - Phase 8: 前端集成与任务下发
 * 展示真实的在线 Agent 列表
 */

"use client"

import { useState, useEffect } from "react"
import { useToast } from "@/hooks/use-toast"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { DataTable, Column } from "@/components/common"
import { getAgents, type Agent, isAgentOnline, getDeviceModel } from "@/lib/api/agentService"
import { RefreshCw, Server, Activity, Smartphone } from "lucide-react"

// 格式化相对时间
function formatRelativeTime(dateString?: string): string {
  if (!dateString) return "从未"
  
  const date = new Date(dateString)
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
const columns: Column<Agent>[] = [
  {
    key: "agent_id",
    header: "Agent ID",
    accessor: (item) => (
      <div className="font-mono text-sm">{item.agent_id}</div>
    )
  },
  {
    key: "phone_number",
    header: "手机号",
    accessor: (item) => (
      <div className="text-sm">
        {item.phone_number || <span className="text-muted-foreground">未设置</span>}
      </div>
    )
  },
  {
    key: "device",
    header: "设备型号",
    accessor: (item) => (
      <div className="flex items-center gap-2 text-sm">
        <Smartphone className="h-4 w-4 text-muted-foreground" />
        <span>{getDeviceModel(item)}</span>
      </div>
    )
  },
  {
    key: "status",
    header: "状态",
    accessor: (item) => {
      const online = isAgentOnline(item)
      return (
        <Badge variant={online ? "default" : "secondary"}>
          <div className="flex items-center gap-1">
            <div className={`h-2 w-2 rounded-full ${online ? "bg-green-500" : "bg-gray-400"}`} />
            <span>{item.status}</span>
          </div>
        </Badge>
      )
    }
  },
  {
    key: "last_active_time",
    header: "最后活跃",
    accessor: (item) => (
      <div className="flex items-center gap-1 text-sm text-muted-foreground">
        <Activity className="h-3 w-3" />
        <span>{formatRelativeTime(item.last_active_time)}</span>
      </div>
    )
  },
  {
    key: "current_task_id",
    header: "当前任务",
    accessor: (item) => (
      <div className="text-sm">
        {item.current_task_id ? (
          <Badge variant="outline" className="font-mono text-xs">
            {item.current_task_id.slice(0, 8)}...
          </Badge>
        ) : (
          <span className="text-muted-foreground">空闲</span>
        )}
      </div>
    )
  }
]

export default function AgentsPage() {
  const { toast } = useToast()
  const [agents, setAgents] = useState<Agent[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  
  const fetchAgents = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await getAgents()
      setAgents(data)
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "加载失败"
      setError(errorMessage)
      toast({
        title: "加载失败",
        description: errorMessage,
        variant: "destructive"
      })
    } finally {
      setLoading(false)
    }
  }
  
  useEffect(() => {
    fetchAgents()
    
    // 每 30 秒自动刷新
    const interval = setInterval(fetchAgents, 30000)
    return () => clearInterval(interval)
  }, [])
  
  // 统计在线 Agent 数量
  const onlineCount = agents.filter(agent => isAgentOnline(agent)).length
  
  return (
    <div className="container mx-auto py-6 space-y-4">
      {/* 标题和操作栏 */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Server className="h-6 w-6" />
          <div>
            <h1 className="text-2xl font-bold">Agent 管理</h1>
            <p className="text-sm text-muted-foreground">
              在线: {onlineCount} / {agents.length}
            </p>
          </div>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={fetchAgents}
          disabled={loading}
        >
          <RefreshCw className={`h-4 w-4 mr-2 ${loading ? "animate-spin" : ""}`} />
          刷新
        </Button>
      </div>
      
      {/* 数据表格 */}
      <DataTable
        data={agents}
        columns={columns}
        loading={loading}
        error={error}
        searchPlaceholder="搜索 Agent ID 或手机号..."
        onSearchChange={(value) => {
          // 简单的客户端搜索
          // 实际应该使用服务端搜索
        }}
      />
    </div>
  )
}

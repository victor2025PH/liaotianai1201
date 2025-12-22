/**
 * 演出配置弹窗组件
 * 用于配置场景执行时的 Agent 映射
 */

"use client"

import * as React from "react"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import { Input } from "@/components/ui/input"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { useAgentStatus } from "@/hooks/useWebSocket"
import { Loader2 } from "lucide-react"
import { useToast } from "@/hooks/use-toast"
import { executeScenario, type TheaterScenario, type TheaterExecutionCreate } from "@/lib/api/theater"

export interface ExecutionDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  scenario: TheaterScenario | null
  onSuccess?: () => void
}

export function ExecutionDialog({
  open,
  onOpenChange,
  scenario,
  onSuccess
}: ExecutionDialogProps) {
  const { agents, onlineAgents } = useAgentStatus()
  const { toast } = useToast()
  const [loading, setLoading] = React.useState(false)
  const [groupId, setGroupId] = React.useState("")
  const [agentMapping, setAgentMapping] = React.useState<Record<string, string>>({})
  
  // 初始化 Agent 映射
  React.useEffect(() => {
    if (scenario && open) {
      const mapping: Record<string, string> = {}
      scenario.roles.forEach(role => {
        // 默认选择第一个在线 Agent（如果有）
        if (onlineAgents && onlineAgents.length > 0 && !mapping[role]) {
          mapping[role] = onlineAgents[0]
        }
      })
      setAgentMapping(mapping)
      setGroupId("")
    }
  }, [scenario, open, onlineAgents])
  
  // 更新角色映射
  const updateMapping = React.useCallback((role: string, agentId: string) => {
    setAgentMapping(prev => ({
      ...prev,
      [role]: agentId
    }))
  }, [])
  
  // 提交执行
  const handleSubmit = React.useCallback(async () => {
    if (!scenario) return
    
    // 验证群组ID
    if (!groupId.trim()) {
      toast({
        title: "验证失败",
        description: "请输入目标群组ID",
        variant: "destructive"
      })
      return
    }
    
    // 验证所有角色都已映射
    const unmappedRoles = scenario.roles.filter(role => !agentMapping[role])
    if (unmappedRoles.length > 0) {
      toast({
        title: "验证失败",
        description: `以下角色未分配 Agent: ${unmappedRoles.join(", ")}`,
        variant: "destructive"
      })
      return
    }
    
    setLoading(true)
    try {
      const executionData: TheaterExecutionCreate = {
        scenario_id: scenario.id,
        group_id: groupId.trim(),
        agent_mapping: agentMapping
      }
      
      await executeScenario(executionData)
      
      toast({
        title: "执行成功",
        description: `场景 "${scenario.name}" 已开始执行`
      })
      
      onOpenChange(false)
      onSuccess?.()
    } catch (error) {
      toast({
        title: "执行失败",
        description: error instanceof Error ? error.message : "未知错误",
        variant: "destructive"
      })
    } finally {
      setLoading(false)
    }
  }, [scenario, groupId, agentMapping, toast, onOpenChange, onSuccess])
  
  if (!scenario) return null
  
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>执行场景: {scenario.name}</DialogTitle>
          <DialogDescription>
            配置 Agent 映射和目标群组，然后开始执行
          </DialogDescription>
        </DialogHeader>
        
        <div className="space-y-6 py-4">
          {/* 目标群组ID */}
          <div className="space-y-2">
            <Label htmlFor="group-id">目标群组ID</Label>
            <Input
              id="group-id"
              value={groupId}
              onChange={(e) => setGroupId(e.target.value)}
              placeholder="例如: -1001234567890"
            />
            <p className="text-xs text-muted-foreground">
              输入 Telegram 群组的 ID（通常是负数）
            </p>
          </div>
          
          {/* Agent 映射 */}
          <div className="space-y-4">
            <Label>角色 - Agent 映射</Label>
            
            {scenario.roles.length === 0 ? (
              <div className="text-sm text-muted-foreground p-3 bg-muted rounded-md">
                该场景没有定义角色
              </div>
            ) : (
              <div className="space-y-3">
                {scenario.roles.map((role) => {
                  const currentAgentId = agentMapping[role]
                  const currentAgent = currentAgentId && agents ? agents[currentAgentId] : null
                  
                  return (
                    <div key={role} className="space-y-2">
                      <Label htmlFor={`agent-${role}`} className="text-sm">
                        {role}
                      </Label>
                      <Select
                        value={currentAgentId || ""}
                        onValueChange={(value) => updateMapping(role, value)}
                      >
                        <SelectTrigger id={`agent-${role}`}>
                          <SelectValue placeholder="选择 Agent" />
                        </SelectTrigger>
                        <SelectContent>
                          {!onlineAgents || onlineAgents.length === 0 ? (
                            <SelectItem value="" disabled>
                              没有在线 Agent
                            </SelectItem>
                          ) : (
                            onlineAgents.map((agentId) => {
                              const agent = agents ? agents[agentId] : undefined
                              return (
                                <SelectItem key={agentId} value={agentId}>
                                  <div className="flex items-center gap-2">
                                    <div className="h-2 w-2 rounded-full bg-green-500" />
                                    <span>{agentId}</span>
                                    {agent?.metadata?.name && (
                                      <span className="text-xs text-muted-foreground">
                                        ({agent.metadata.name})
                                      </span>
                                    )}
                                  </div>
                                </SelectItem>
                              )
                            })
                          )}
                        </SelectContent>
                      </Select>
                      {currentAgent && (
                        <p className="text-xs text-muted-foreground">
                          状态: {currentAgent.status === "online" ? "🟢 在线" : "🔴 离线"}
                          {currentAgent.latency && ` | 延迟: ${currentAgent.latency}ms`}
                        </p>
                      )}
                    </div>
                  )
                })}
              </div>
            )}
            
            {(!onlineAgents || onlineAgents.length === 0) && (
              <div className="text-sm text-amber-600 p-3 bg-amber-50 dark:bg-amber-950 rounded-md border border-amber-200 dark:border-amber-800">
                ⚠️ 当前没有在线 Agent，无法执行场景
              </div>
            )}
          </div>
        </div>
        
        <DialogFooter>
          <Button
            variant="outline"
            onClick={() => onOpenChange(false)}
            disabled={loading}
          >
            取消
          </Button>
          <Button
            onClick={handleSubmit}
            disabled={loading || !onlineAgents || onlineAgents.length === 0}
          >
            {loading && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
            开始执行
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

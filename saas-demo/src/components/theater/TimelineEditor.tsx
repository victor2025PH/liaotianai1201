/**
 * 时间轴编辑器组件
 * 用于创建和编辑剧场场景的时间轴动作
 */

"use client"

import * as React from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Textarea } from "@/components/ui/textarea"
import { Plus, Trash2, ArrowUp, ArrowDown } from "lucide-react"
import { cn } from "@/lib/utils"
import type { TimelineAction } from "@/lib/api/theater"

export interface TimelineEditorProps {
  value: TimelineAction[]
  onChange: (actions: TimelineAction[]) => void
  roles: string[]
  className?: string
}

export function TimelineEditor({
  value,
  onChange,
  roles,
  className
}: TimelineEditorProps) {
  const [actions, setActions] = React.useState<TimelineAction[]>(value || [])
  
  // 同步外部值变化
  React.useEffect(() => {
    setActions(value || [])
  }, [value])
  
  // 更新动作列表
  const updateActions = React.useCallback((newActions: TimelineAction[]) => {
    // 按时间偏移排序
    const sorted = [...newActions].sort((a, b) => a.time_offset - b.time_offset)
    setActions(sorted)
    onChange(sorted)
  }, [onChange])
  
  // 添加新动作
  const addAction = React.useCallback(() => {
    const newAction: TimelineAction = {
      time_offset: actions.length > 0 
        ? Math.max(...actions.map(a => a.time_offset)) + 2 
        : 0,
      role: roles[0] || "",
      content: "",
      action: "send_message"
    }
    updateActions([...actions, newAction])
  }, [actions, roles, updateActions])
  
  // 删除动作
  const removeAction = React.useCallback((index: number) => {
    updateActions(actions.filter((_, i) => i !== index))
  }, [actions, updateActions])
  
  // 更新动作字段
  const updateAction = React.useCallback((
    index: number,
    field: keyof TimelineAction,
    newValue: any
  ) => {
    const newActions = [...actions]
    newActions[index] = {
      ...newActions[index],
      [field]: newValue
    }
    updateActions(newActions)
  }, [actions, updateActions])
  
  // 上移/下移动作
  const moveAction = React.useCallback((index: number, direction: "up" | "down") => {
    if (direction === "up" && index === 0) return
    if (direction === "down" && index === actions.length - 1) return
    
    const newActions = [...actions]
    const targetIndex = direction === "up" ? index - 1 : index + 1
    ;[newActions[index], newActions[targetIndex]] = [newActions[targetIndex], newActions[index]]
    updateActions(newActions)
  }, [actions, updateActions])
  
  return (
    <div className={cn("space-y-4", className)}>
      <div className="flex items-center justify-between">
        <Label>时间轴动作</Label>
        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={addAction}
          disabled={roles.length === 0}
        >
          <Plus className="h-4 w-4 mr-1" />
          添加动作
        </Button>
      </div>
      
      {roles.length === 0 && (
        <div className="text-sm text-muted-foreground p-3 bg-muted rounded-md">
          请先添加角色，然后才能添加时间轴动作
        </div>
      )}
      
      {actions.length === 0 ? (
        <div className="text-sm text-muted-foreground p-4 border border-dashed rounded-md text-center">
          暂无动作，点击"添加动作"开始创建
        </div>
      ) : (
        <div className="space-y-3">
          {actions.map((action, index) => (
            <div
              key={index}
              className="p-4 border rounded-lg space-y-3 bg-card"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium text-muted-foreground">
                    动作 #{index + 1}
                  </span>
                  <span className="text-xs text-muted-foreground">
                    (第 {action.time_offset} 秒)
                  </span>
                </div>
                <div className="flex items-center gap-1">
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    onClick={() => moveAction(index, "up")}
                    disabled={index === 0}
                  >
                    <ArrowUp className="h-3 w-3" />
                  </Button>
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    onClick={() => moveAction(index, "down")}
                    disabled={index === actions.length - 1}
                  >
                    <ArrowDown className="h-3 w-3" />
                  </Button>
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    onClick={() => removeAction(index)}
                  >
                    <Trash2 className="h-4 w-4 text-destructive" />
                  </Button>
                </div>
              </div>
              
              <div className="grid grid-cols-3 gap-3">
                <div className="space-y-1">
                  <Label htmlFor={`time-offset-${index}`} className="text-xs">
                    时间偏移 (秒)
                  </Label>
                  <Input
                    id={`time-offset-${index}`}
                    type="number"
                    min="0"
                    value={action.time_offset}
                    onChange={(e) => updateAction(
                      index,
                      "time_offset",
                      parseInt(e.target.value) || 0
                    )}
                    placeholder="0"
                  />
                </div>
                
                <div className="space-y-1">
                  <Label htmlFor={`role-${index}`} className="text-xs">
                    角色
                  </Label>
                  <Select
                    value={action.role}
                    onValueChange={(value) => updateAction(index, "role", value)}
                  >
                    <SelectTrigger id={`role-${index}`}>
                      <SelectValue placeholder="选择角色" />
                    </SelectTrigger>
                    <SelectContent>
                      {roles.map((role) => (
                        <SelectItem key={role} value={role}>
                          {role}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                
                <div className="space-y-1">
                  <Label htmlFor={`action-${index}`} className="text-xs">
                    动作类型
                  </Label>
                  <Select
                    value={action.action || "send_message"}
                    onValueChange={(value) => updateAction(index, "action", value)}
                  >
                    <SelectTrigger id={`action-${index}`}>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="send_message">发送消息</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              
              <div className="space-y-1">
                <Label htmlFor={`content-${index}`} className="text-xs">
                  内容
                </Label>
                <Textarea
                  id={`content-${index}`}
                  value={action.content}
                  onChange={(e) => updateAction(index, "content", e.target.value)}
                  placeholder="输入消息内容..."
                  rows={2}
                />
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

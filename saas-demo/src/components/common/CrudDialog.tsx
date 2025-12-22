/**
 * 通用 CRUD 对话框组件
 * 支持 Create 和 Edit 模式
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
import { Textarea } from "@/components/ui/textarea"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Loader2 } from "lucide-react"
import { cn } from "@/lib/utils"

// 表单字段定义
export interface FormField {
  name: string
  label: string
  type?: "text" | "textarea" | "number" | "select" | "checkbox" | "date"
  placeholder?: string
  required?: boolean
  options?: { label: string; value: string | number }[]
  render?: (value: any, onChange: (value: any) => void) => React.ReactNode
  validation?: (value: any) => string | null
}

// CrudDialog Props
export interface CrudDialogProps<T> {
  open: boolean
  onOpenChange: (open: boolean) => void
  mode: "create" | "edit"
  title: string
  description?: string
  fields: FormField[]
  initialData?: Partial<T>
  onSubmit: (data: Partial<T>) => Promise<void> | void
  loading?: boolean
  submitLabel?: string
  cancelLabel?: string
  className?: string
  maxWidth?: "sm" | "md" | "lg" | "xl" | "2xl"
}

/**
 * 通用 CRUD 对话框组件
 */
export function CrudDialog<T extends Record<string, any>>({
  open,
  onOpenChange,
  mode,
  title,
  description,
  fields,
  initialData,
  onSubmit,
  loading = false,
  submitLabel,
  cancelLabel = "取消",
  className,
  maxWidth = "lg"
}: CrudDialogProps<T>) {
  const [formData, setFormData] = React.useState<Partial<T>>(initialData || {})
  const [errors, setErrors] = React.useState<Record<string, string>>({})
  
  // 初始化表单数据
  React.useEffect(() => {
    if (open) {
      setFormData(initialData || {})
      setErrors({})
    }
  }, [open, initialData])
  
  // 更新字段值
  const updateField = React.useCallback((name: string, value: any) => {
    setFormData(prev => ({ ...prev, [name]: value }))
    // 清除该字段的错误
    if (errors[name]) {
      setErrors(prev => {
        const newErrors = { ...prev }
        delete newErrors[name]
        return newErrors
      })
    }
  }, [errors])
  
  // 验证表单
  const validate = React.useCallback((): boolean => {
    const newErrors: Record<string, string> = {}
    
    fields.forEach(field => {
      const value = formData[field.name]
      
      // 必填验证
      if (field.required && (value === undefined || value === null || value === "")) {
        newErrors[field.name] = `${field.label} 是必填项`
        return
      }
      
      // 自定义验证
      if (field.validation && value !== undefined && value !== null && value !== "") {
        const error = field.validation(value)
        if (error) {
          newErrors[field.name] = error
        }
      }
    })
    
    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }, [fields, formData])
  
  // 提交表单
  const handleSubmit = React.useCallback(async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!validate()) {
      return
    }
    
    try {
      await onSubmit(formData)
      onOpenChange(false)
    } catch (error) {
      console.error("[CrudDialog] 提交失败:", error)
    }
  }, [formData, validate, onSubmit, onOpenChange])
  
  // 渲染字段
  const renderField = React.useCallback((field: FormField) => {
    const value = formData[field.name]
    const error = errors[field.name]
    
    // 自定义渲染
    if (field.render) {
      return (
        <div key={field.name} className="space-y-2">
          <label className="text-sm font-medium">
            {field.label}
            {field.required && <span className="text-destructive ml-1">*</span>}
          </label>
          {field.render(value, (newValue) => updateField(field.name, newValue))}
          {error && (
            <p className="text-sm text-destructive">{error}</p>
          )}
        </div>
      )
    }
    
    // 默认渲染
    switch (field.type) {
      case "textarea":
        return (
          <div key={field.name} className="space-y-2">
            <label className="text-sm font-medium">
              {field.label}
              {field.required && <span className="text-destructive ml-1">*</span>}
            </label>
            <Textarea
              value={value || ""}
              onChange={(e) => updateField(field.name, e.target.value)}
              placeholder={field.placeholder}
              className={cn(
                "min-h-[80px]",
                error && "border-destructive"
              )}
            />
            {error && (
              <p className="text-sm text-destructive">{error}</p>
            )}
          </div>
        )
      
      case "select":
        return (
          <div key={field.name} className="space-y-2">
            <label className="text-sm font-medium">
              {field.label}
              {field.required && <span className="text-destructive ml-1">*</span>}
            </label>
            <Select
              value={String(value || "")}
              onValueChange={(val) => updateField(field.name, val)}
            >
              <SelectTrigger className={cn(error && "border-destructive")}>
                <SelectValue placeholder="请选择..." />
              </SelectTrigger>
              <SelectContent>
                {field.options?.map(option => (
                  <SelectItem key={option.value} value={String(option.value)}>
                    {option.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            {error && (
              <p className="text-sm text-destructive">{error}</p>
            )}
          </div>
        )
      
      case "checkbox":
        return (
          <div key={field.name} className="flex items-center space-x-2">
            <input
              type="checkbox"
              checked={value || false}
              onChange={(e) => updateField(field.name, e.target.checked)}
              className="rounded border-gray-300"
            />
            <label className="text-sm font-medium">
              {field.label}
              {field.required && <span className="text-destructive ml-1">*</span>}
            </label>
            {error && (
              <p className="text-sm text-destructive ml-2">{error}</p>
            )}
          </div>
        )
      
      default:
        return (
          <div key={field.name} className="space-y-2">
            <label className="text-sm font-medium">
              {field.label}
              {field.required && <span className="text-destructive ml-1">*</span>}
            </label>
            <input
              type={field.type || "text"}
              value={value || ""}
              onChange={(e) => {
                const newValue = field.type === "number" 
                  ? (e.target.value === "" ? undefined : Number(e.target.value))
                  : e.target.value
                updateField(field.name, newValue)
              }}
              placeholder={field.placeholder}
              className={cn(
                "flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm transition-colors placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring",
                error && "border-destructive"
              )}
            />
            {error && (
              <p className="text-sm text-destructive">{error}</p>
            )}
          </div>
        )
    }
  }, [formData, errors, updateField])
  
  const defaultSubmitLabel = mode === "create" ? "创建" : "保存"
  
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className={cn("max-w-2xl", className)}>
        <DialogHeader>
          <DialogTitle>{title}</DialogTitle>
          {description && (
            <DialogDescription>{description}</DialogDescription>
          )}
        </DialogHeader>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid gap-4 py-4">
            {fields.map(field => renderField(field))}
          </div>
          
          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
              disabled={loading}
            >
              {cancelLabel}
            </Button>
            <Button
              type="submit"
              disabled={loading}
            >
              {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              {submitLabel || defaultSubmitLabel}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}

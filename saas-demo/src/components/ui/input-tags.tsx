/**
 * 标签输入组件 - 支持输入多个关键词
 */

"use client"

import * as React from "react"
import { X } from "lucide-react"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { cn } from "@/lib/utils"

export interface InputTagsProps {
  value: string[]
  onChange: (tags: string[]) => void
  placeholder?: string
  className?: string
  maxTags?: number
}

export function InputTags({
  value,
  onChange,
  placeholder = "输入关键词后按回车添加",
  className,
  maxTags
}: InputTagsProps) {
  const [inputValue, setInputValue] = React.useState("")
  const inputRef = React.useRef<HTMLInputElement>(null)
  
  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" || e.key === ",") {
      e.preventDefault()
      addTag(inputValue.trim())
    } else if (e.key === "Backspace" && inputValue === "" && value.length > 0) {
      // 删除最后一个标签
      removeTag(value.length - 1)
    }
  }
  
  const addTag = (tag: string) => {
    if (!tag) return
    
    // 检查是否已存在
    if (value.includes(tag)) {
      setInputValue("")
      return
    }
    
    // 检查最大数量
    if (maxTags && value.length >= maxTags) {
      return
    }
    
    onChange([...value, tag])
    setInputValue("")
  }
  
  const removeTag = (index: number) => {
    onChange(value.filter((_, i) => i !== index))
  }
  
  const handlePaste = (e: React.ClipboardEvent<HTMLInputElement>) => {
    e.preventDefault()
    const pastedText = e.clipboardData.getData("text")
    const tags = pastedText
      .split(/[,\n]/)
      .map(tag => tag.trim())
      .filter(tag => tag && !value.includes(tag))
    
    if (tags.length > 0) {
      const newTags = [...value, ...tags]
      if (maxTags) {
        onChange(newTags.slice(0, maxTags))
      } else {
        onChange(newTags)
      }
      setInputValue("")
    }
  }
  
  return (
    <div className={cn("space-y-2", className)}>
      <div
        className="flex flex-wrap gap-2 min-h-[2.5rem] w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-sm transition-colors focus-within:outline-none focus-within:ring-1 focus-within:ring-ring"
        onClick={() => inputRef.current?.focus()}
      >
        {value.map((tag, index) => (
          <Badge
            key={index}
            variant="secondary"
            className="gap-1 pr-1"
          >
            {tag}
            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation()
                removeTag(index)
              }}
              className="ml-1 rounded-full hover:bg-muted"
            >
              <X className="h-3 w-3" />
            </button>
          </Badge>
        ))}
        <Input
          ref={inputRef}
          type="text"
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyDown={handleKeyDown}
          onPaste={handlePaste}
          placeholder={value.length === 0 ? placeholder : ""}
          className="flex-1 border-0 focus-visible:ring-0 focus-visible:ring-offset-0 h-auto p-0 min-w-[120px]"
        />
      </div>
      {maxTags && (
        <p className="text-xs text-muted-foreground">
          已添加 {value.length} / {maxTags} 个关键词
        </p>
      )}
    </div>
  )
}

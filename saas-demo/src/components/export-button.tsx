"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
  DropdownMenuItem,
} from "@/components/ui/dropdown-menu"
import { Download, FileSpreadsheet, FileText, File } from "lucide-react"
import { useToast } from "@/hooks/use-toast"
import type { ExportFormat } from "@/lib/api/group-ai"

interface ExportButtonProps {
  onExport: (format: ExportFormat) => Promise<void>
  label?: string
  disabled?: boolean
}

export function ExportButton({ onExport, label = "導出", disabled = false }: ExportButtonProps) {
  const { toast } = useToast()
  const [exporting, setExporting] = useState(false)

  const handleExport = async (format: ExportFormat) => {
    try {
      setExporting(true)
      await onExport(format)
      toast({
        title: "導出成功",
        description: `數據已導出為 ${format.toUpperCase()} 格式`,
      })
    } catch (error: any) {
      toast({
        title: "導出失敗",
        description: error.message || "無法導出數據",
        variant: "destructive",
      })
    } finally {
      setExporting(false)
    }
  }

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="outline" disabled={disabled || exporting}>
          <Download className="mr-2 h-4 w-4" />
          {exporting ? "導出中..." : label}
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        <DropdownMenuLabel>選擇導出格式</DropdownMenuLabel>
        <DropdownMenuSeparator />
        <DropdownMenuItem onClick={() => handleExport("csv")}>
          <File className="mr-2 h-4 w-4" />
          CSV 格式
        </DropdownMenuItem>
        <DropdownMenuItem onClick={() => handleExport("excel")}>
          <FileSpreadsheet className="mr-2 h-4 w-4" />
          Excel 格式
        </DropdownMenuItem>
        <DropdownMenuItem onClick={() => handleExport("pdf")}>
          <FileText className="mr-2 h-4 w-4" />
          PDF 格式
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}


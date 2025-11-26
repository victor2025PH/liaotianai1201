"use client"

import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Home, ArrowLeft, Search } from "lucide-react"

export default function NotFound() {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-background px-4">
      <div className="text-center space-y-6 max-w-md">
        {/* 404 大字 */}
        <div className="relative">
          <h1 className="text-[150px] font-bold text-primary/10 leading-none select-none">
            404
          </h1>
          <div className="absolute inset-0 flex items-center justify-center">
            <Search className="h-20 w-20 text-primary/30" />
          </div>
        </div>
        
        {/* 標題和描述 */}
        <div className="space-y-2">
          <h2 className="text-2xl font-bold">頁面未找到</h2>
          <p className="text-muted-foreground">
            抱歉，您訪問的頁面不存在或已被移除。
          </p>
        </div>
        
        {/* 操作按鈕 */}
        <div className="flex flex-col sm:flex-row gap-3 justify-center">
          <Button asChild>
            <Link href="/">
              <Home className="mr-2 h-4 w-4" />
              返回首頁
            </Link>
          </Button>
          <Button variant="outline" onClick={() => window.history.back()}>
            <ArrowLeft className="mr-2 h-4 w-4" />
            返回上一頁
          </Button>
        </div>
        
        {/* 提示 */}
        <p className="text-sm text-muted-foreground pt-4">
          如果您認為這是一個錯誤，請聯繫管理員
        </p>
      </div>
    </div>
  )
}






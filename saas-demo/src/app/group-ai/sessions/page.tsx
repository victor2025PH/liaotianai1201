"use client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Construction, MessageSquare } from "lucide-react"

export default function SessionsPage() {
  return (
    <div className="container mx-auto p-6 space-y-6">
      <div className="flex items-center gap-2">
        <MessageSquare className="h-6 w-6" />
        <h1 className="text-3xl font-bold">会话管理</h1>
      </div>
      
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Construction className="h-5 w-5 text-yellow-500" />
            功能开发中
          </CardTitle>
          <CardDescription>
            此页面正在开发中，敬请期待
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col items-center justify-center py-12 text-center space-y-4">
            <Construction className="h-16 w-16 text-yellow-500" />
            <p className="text-lg text-muted-foreground">
              会话管理功能即将上线
            </p>
            <p className="text-sm text-muted-foreground">
              我们将在此页面提供会话记录查看、搜索和管理功能
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}


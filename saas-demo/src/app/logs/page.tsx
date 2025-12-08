"use client"

import { useEffect } from "react"
import { useRouter } from "next/navigation"

export default function LogsPage() {
  const router = useRouter()
  
  useEffect(() => {
    // 重定向到 /group-ai/logs
    router.replace("/group-ai/logs")
  }, [router])
  
  return (
    <div className="flex h-screen items-center justify-center">
      <div className="text-center">
        <div className="mb-4 h-8 w-8 animate-spin rounded-full border-4 border-gray-300 border-t-blue-600 mx-auto"></div>
        <p className="text-sm text-gray-500">正在跳转...</p>
      </div>
    </div>
  )
}

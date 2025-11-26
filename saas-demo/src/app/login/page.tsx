/**
 * 登錄頁面
 */
"use client"

import { useState, useEffect, Suspense } from "react"
import { useRouter, useSearchParams } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { useToast } from "@/hooks/use-toast"
import { login, setToken } from "@/lib/api/auth"
import { Shield, Loader2 } from "lucide-react"

function LoginForm() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const { toast } = useToast()
  const [formData, setFormData] = useState({
    username: "",
    password: "",
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // 开发模式：支持通过URL参数自动登录（仅用于测试）
  useEffect(() => {
    if (typeof window !== "undefined") {
      const autoToken = searchParams.get("token")
      if (autoToken && process.env.NODE_ENV === "development") {
        setToken(autoToken)
        toast({
          title: "自动登录成功",
          description: "正在跳转...",
        })
        router.push("/")
        return
      }
      
      // 自动填充默认账号
      if (!formData.username && !formData.password) {
        setFormData({
          username: "admin@example.com",
          password: "changeme123",
        })
      }
    }
  }, [searchParams, router, toast])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)

    if (!formData.username || !formData.password) {
      setError("請輸入郵箱和密碼")
      return
    }

    try {
      setLoading(true)
      const response = await login({
        username: formData.username,
        password: formData.password,
      })

      // 保存 token
      setToken(response.access_token)

      toast({
        title: "登錄成功",
        description: "正在跳轉...",
      })

      // 跳轉到首頁
      router.push("/")
    } catch (err) {
      const message = err instanceof Error ? err.message : "登錄失敗，請檢查郵箱和密碼"
      setError(message)
      toast({
        title: "登錄失敗",
        description: message,
        variant: "destructive",
      })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-background to-muted p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="space-y-1">
          <div className="flex items-center justify-center mb-4">
            <Shield className="h-12 w-12 text-primary" />
          </div>
          <CardTitle className="text-2xl text-center">登錄</CardTitle>
          <CardDescription className="text-center">
            聊天 AI 控制台
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            {error && (
              <Alert variant="destructive">
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}

            <div className="space-y-2">
              <Label htmlFor="username">郵箱</Label>
              <Input
                id="username"
                type="email"
                placeholder="admin@example.com"
                value={formData.username}
                onChange={(e) =>
                  setFormData({ ...formData, username: e.target.value })
                }
                disabled={loading}
                required
                autoFocus
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="password">密碼</Label>
              <Input
                id="password"
                type="password"
                placeholder="輸入密碼"
                value={formData.password}
                onChange={(e) =>
                  setFormData({ ...formData, password: e.target.value })
                }
                disabled={loading}
                required
              />
            </div>

            <Button
              type="submit"
              className="w-full"
              disabled={loading}
            >
              {loading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  登錄中...
                </>
              ) : (
                "登錄"
              )}
            </Button>
          </form>

          <div className="mt-6 text-center text-sm text-muted-foreground">
            <p>默認賬號：</p>
            <p className="font-mono">admin@example.com</p>
            <p className="font-mono">changeme123</p>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

export default function LoginPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    }>
      <LoginForm />
    </Suspense>
  )
}


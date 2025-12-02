"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { useToast } from "@/hooks/use-toast"
import { Download, Copy, Check, Server, Laptop, Terminal } from "lucide-react"
import { getApiBaseUrl } from "@/lib/api/config"

const API_BASE = getApiBaseUrl()

interface DeployConfig {
  node_id: string
  server_url: string
  api_key: string
  heartbeat_interval: number
  telegram_api_id: string
  telegram_api_hash: string
}

export default function WorkerDeployPage() {
  const { toast } = useToast()
  const [loading, setLoading] = useState(false)
  const [copied, setCopied] = useState<string | null>(null)
  const [scripts, setScripts] = useState<any>(null)
  
  const [config, setConfig] = useState<DeployConfig>({
    node_id: `worker_${Date.now().toString(36)}`,
    server_url: typeof window !== 'undefined' ? `${window.location.protocol}//${window.location.host}` : "https://aikz.usdt2026.cc",
    api_key: "",
    heartbeat_interval: 30,
    telegram_api_id: "",
    telegram_api_hash: ""
  })

  const generatePackage = async () => {
    try {
      setLoading(true)
      const { fetchWithAuth } = await import("@/lib/api/client")
      const res = await fetchWithAuth(`${API_BASE}/workers/deploy-package`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(config)
      })
      
      if (!res.ok) {
        throw new Error(`HTTP ${res.status}`)
      }
      
      const data = await res.json()
      setScripts(data.scripts)
      
      toast({
        title: "✅ 生成成功",
        description: "部署腳本已生成，請下載使用"
      })
    } catch (error) {
      toast({
        title: "❌ 生成失敗",
        description: String(error),
        variant: "destructive"
      })
    } finally {
      setLoading(false)
    }
  }

  const copyToClipboard = async (text: string, name: string) => {
    try {
      await navigator.clipboard.writeText(text)
      setCopied(name)
      setTimeout(() => setCopied(null), 2000)
      toast({ title: "已複製到剪貼板" })
    } catch (error) {
      toast({ title: "複製失敗", variant: "destructive" })
    }
  }

  const downloadFile = (content: string, filename: string) => {
    const blob = new Blob([content], { type: "text/plain;charset=utf-8" })
    const url = URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url
    a.download = filename
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
    toast({ title: `已下載 ${filename}` })
  }

  const downloadAllFiles = () => {
    if (!scripts) return
    downloadFile(scripts.windows, "start_worker.bat")
    downloadFile(scripts.linux, "start_worker.sh")
    downloadFile(scripts.worker_client, "worker_client.py")
    toast({ title: "✅ 所有文件已下載" })
  }

  return (
    <div className="container mx-auto p-6 max-w-4xl">
      <div className="mb-6">
        <h1 className="text-3xl font-bold flex items-center gap-2">
          <Server className="h-8 w-8" />
          Worker 節點部署
        </h1>
        <p className="text-muted-foreground mt-2">
          配置並生成 Worker 節點自動運行包，用於在遠端電腦上運行 Telegram 帳號
        </p>
      </div>

      <div className="grid gap-6">
        {/* 配置表單 */}
        <Card>
          <CardHeader>
            <CardTitle>節點配置</CardTitle>
            <CardDescription>填寫 Worker 節點的環境變量配置</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="node_id">節點 ID *</Label>
                <Input
                  id="node_id"
                  value={config.node_id}
                  onChange={(e) => setConfig({ ...config, node_id: e.target.value })}
                  placeholder="worker_001"
                />
                <p className="text-xs text-muted-foreground">每個節點的唯一標識</p>
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="server_url">服務器地址 *</Label>
                <Input
                  id="server_url"
                  value={config.server_url}
                  onChange={(e) => setConfig({ ...config, server_url: e.target.value })}
                  placeholder="https://aikz.usdt2026.cc"
                />
                <p className="text-xs text-muted-foreground">主控制台地址</p>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="api_key">API 密鑰（可選）</Label>
                <Input
                  id="api_key"
                  type="password"
                  value={config.api_key}
                  onChange={(e) => setConfig({ ...config, api_key: e.target.value })}
                  placeholder="留空則不使用認證"
                />
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="heartbeat_interval">心跳間隔（秒）</Label>
                <Input
                  id="heartbeat_interval"
                  type="number"
                  value={config.heartbeat_interval}
                  onChange={(e) => setConfig({ ...config, heartbeat_interval: parseInt(e.target.value) || 30 })}
                />
              </div>
            </div>

            <div className="border-t pt-4 mt-4">
              <h4 className="font-medium mb-3">Telegram API 配置（可選）</h4>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="telegram_api_id">API ID</Label>
                  <Input
                    id="telegram_api_id"
                    value={config.telegram_api_id}
                    onChange={(e) => setConfig({ ...config, telegram_api_id: e.target.value })}
                    placeholder="從 my.telegram.org 獲取"
                  />
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="telegram_api_hash">API Hash</Label>
                  <Input
                    id="telegram_api_hash"
                    type="password"
                    value={config.telegram_api_hash}
                    onChange={(e) => setConfig({ ...config, telegram_api_hash: e.target.value })}
                    placeholder="從 my.telegram.org 獲取"
                  />
                </div>
              </div>
              <p className="text-xs text-muted-foreground mt-2">
                訪問 <a href="https://my.telegram.org" target="_blank" className="text-blue-500 hover:underline">my.telegram.org</a> 獲取 API 憑證
              </p>
            </div>

            <Button onClick={generatePackage} disabled={loading} className="w-full mt-4">
              {loading ? "生成中..." : "生成部署包"}
            </Button>
          </CardContent>
        </Card>

        {/* 生成的腳本 */}
        {scripts && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <span>部署腳本</span>
                <Button onClick={downloadAllFiles} variant="outline" size="sm">
                  <Download className="h-4 w-4 mr-2" />
                  下載全部文件
                </Button>
              </CardTitle>
              <CardDescription>
                將所有文件下載到同一目錄，然後運行對應系統的啟動腳本
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Tabs defaultValue="windows">
                <TabsList className="grid w-full grid-cols-3">
                  <TabsTrigger value="windows">
                    <Laptop className="h-4 w-4 mr-2" />
                    Windows
                  </TabsTrigger>
                  <TabsTrigger value="linux">
                    <Terminal className="h-4 w-4 mr-2" />
                    Linux/Mac
                  </TabsTrigger>
                  <TabsTrigger value="python">
                    <Server className="h-4 w-4 mr-2" />
                    Worker 客戶端
                  </TabsTrigger>
                </TabsList>

                <TabsContent value="windows" className="mt-4">
                  <div className="flex justify-end gap-2 mb-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => copyToClipboard(scripts.windows, "windows")}
                    >
                      {copied === "windows" ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => downloadFile(scripts.windows, "start_worker.bat")}
                    >
                      <Download className="h-4 w-4" />
                    </Button>
                  </div>
                  <pre className="bg-muted p-4 rounded-lg overflow-auto max-h-96 text-xs">
                    {scripts.windows}
                  </pre>
                </TabsContent>

                <TabsContent value="linux" className="mt-4">
                  <div className="flex justify-end gap-2 mb-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => copyToClipboard(scripts.linux, "linux")}
                    >
                      {copied === "linux" ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => downloadFile(scripts.linux, "start_worker.sh")}
                    >
                      <Download className="h-4 w-4" />
                    </Button>
                  </div>
                  <pre className="bg-muted p-4 rounded-lg overflow-auto max-h-96 text-xs">
                    {scripts.linux}
                  </pre>
                </TabsContent>

                <TabsContent value="python" className="mt-4">
                  <div className="flex justify-end gap-2 mb-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => copyToClipboard(scripts.worker_client, "python")}
                    >
                      {copied === "python" ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => downloadFile(scripts.worker_client, "worker_client.py")}
                    >
                      <Download className="h-4 w-4" />
                    </Button>
                  </div>
                  <pre className="bg-muted p-4 rounded-lg overflow-auto max-h-96 text-xs">
                    {scripts.worker_client}
                  </pre>
                </TabsContent>
              </Tabs>
            </CardContent>
          </Card>
        )}

        {/* 使用說明 */}
        <Card>
          <CardHeader>
            <CardTitle>使用說明</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid md:grid-cols-2 gap-6">
              <div>
                <h4 className="font-medium mb-2 flex items-center gap-2">
                  <Laptop className="h-4 w-4" />
                  Windows 部署
                </h4>
                <ol className="list-decimal list-inside space-y-1 text-sm text-muted-foreground">
                  <li>下載所有文件到同一目錄</li>
                  <li>將 Telegram .session 文件放入 sessions 目錄</li>
                  <li>雙擊 start_worker.bat 運行</li>
                </ol>
              </div>
              <div>
                <h4 className="font-medium mb-2 flex items-center gap-2">
                  <Terminal className="h-4 w-4" />
                  Linux/Mac 部署
                </h4>
                <ol className="list-decimal list-inside space-y-1 text-sm text-muted-foreground">
                  <li>下載所有文件到同一目錄</li>
                  <li>將 Telegram .session 文件放入 sessions 目錄</li>
                  <li>運行: chmod +x start_worker.sh && ./start_worker.sh</li>
                </ol>
              </div>
            </div>
            
            <div className="border-t pt-4">
              <h4 className="font-medium mb-2">後台運行</h4>
              <div className="grid md:grid-cols-2 gap-4 text-sm">
                <div className="bg-muted p-3 rounded">
                  <p className="text-xs text-muted-foreground mb-1">Windows:</p>
                  <code>start /b pythonw worker_client.py</code>
                </div>
                <div className="bg-muted p-3 rounded">
                  <p className="text-xs text-muted-foreground mb-1">Linux:</p>
                  <code>nohup ./start_worker.sh &gt; worker.log 2&gt;&amp;1 &amp;</code>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

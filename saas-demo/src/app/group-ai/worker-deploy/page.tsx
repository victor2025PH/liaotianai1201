"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { useToast } from "@/hooks/use-toast"
import { Download, Copy, Check, Server, Laptop, Terminal, Package, HelpCircle } from "lucide-react"
import { getApiBaseUrl } from "@/lib/api/config"
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip"

const API_BASE = getApiBaseUrl()

interface DeployConfig {
  node_id: string
  server_url: string
  api_key: string
  heartbeat_interval: number
  telegram_api_id: string
  telegram_api_hash: string
}

// 生成友好的節點ID建議
const generateNodeId = () => {
  const adjectives = ["swift", "blue", "red", "smart", "fast", "cool", "nice"]
  const nouns = ["wolf", "tiger", "eagle", "hawk", "fox", "bear", "lion"]
  const adj = adjectives[Math.floor(Math.random() * adjectives.length)]
  const noun = nouns[Math.floor(Math.random() * nouns.length)]
  const num = Math.floor(Math.random() * 100)
  return `worker_${adj}_${noun}_${num}`
}

export default function WorkerDeployPage() {
  const { toast } = useToast()
  const [loading, setLoading] = useState(false)
  const [downloading, setDownloading] = useState(false)
  const [copied, setCopied] = useState<string | null>(null)
  const [scripts, setScripts] = useState<any>(null)
  
  const [config, setConfig] = useState<DeployConfig>({
    node_id: "",
    server_url: typeof window !== 'undefined' ? `${window.location.protocol}//${window.location.host}` : "https://aikz.usdt2026.cc",
    api_key: "",
    heartbeat_interval: 30,
    telegram_api_id: "",
    telegram_api_hash: ""
  })

  // 初始化時生成節點ID
  useEffect(() => {
    setConfig(prev => ({ ...prev, node_id: generateNodeId() }))
  }, [])

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

  // 下載 ZIP 壓縮包
  const downloadZip = async () => {
    if (!scripts) return
    
    setDownloading(true)
    try {
      // 動態導入 JSZip
      const JSZip = (await import("jszip")).default
      const zip = new JSZip()
      
      // 創建 worker-deploy 目錄結構
      const folder = zip.folder(`worker-deploy-${config.node_id}`)
      if (folder) {
        folder.file("start_worker.bat", scripts.windows)
        folder.file("start_worker.sh", scripts.linux)
        folder.file("worker_client.py", scripts.worker_client)
        folder.file("fix_session.py", scripts.fix_session)
        folder.file("create_excel_template.py", scripts.create_excel_template)
        
        // 創建 sessions 目錄（帶一個說明文件）
        const sessionsFolder = folder.folder("sessions")
        if (sessionsFolder) {
          sessionsFolder.file("README.txt", 
`將 Telegram .session 文件放在此目錄

例如：
- 639277358115.session
- 639454959591.session

Session 文件可以通過 Telethon 登入生成

重要提示：
1. Session 文件名必須與 Excel 配置中的 phone 列匹配
2. 如果 Session 文件讀取錯誤，運行: python fix_session.py sessions
3. 創建 Excel 配置模板: python create_excel_template.py
4. Excel 文件必須包含以下列：
   - api_id: Telegram API ID（從 my.telegram.org 獲取）
   - api_hash: Telegram API Hash（從 my.telegram.org 獲取）
   - phone: 電話號碼（必須與 session 文件名匹配）
   - enabled: 1=啟用，0=禁用
`)
        }
        
        // 創建 README
        folder.file("README.md", 
`# Worker 節點部署包

## 節點信息
- 節點 ID: ${config.node_id}
- 服務器: ${config.server_url}
- 心跳間隔: ${config.heartbeat_interval} 秒

## 快速開始

### Windows
1. 將 Telegram .session 文件放入 sessions 目錄
2. 運行 create_excel_template.py 創建 Excel 配置模板
3. 編輯 Excel 文件（${config.node_id}.xlsx），添加：
   - api_id: Telegram API ID（從 my.telegram.org 獲取）
   - api_hash: Telegram API Hash（從 my.telegram.org 獲取）
   - phone: 電話號碼（必須與 session 文件名匹配）
   - enabled: 1=啟用，0=禁用
4. 如果 Session 文件讀取錯誤，運行: python fix_session.py sessions
5. 雙擊 start_worker.bat 運行

### Linux/Mac
1. 將 Telegram .session 文件放入 sessions 目錄
2. 運行 python3 create_excel_template.py 創建 Excel 配置模板
3. 編輯 Excel 文件（${config.node_id}.xlsx），添加 API ID/Hash 和電話號碼
4. 如果 Session 文件讀取錯誤，運行: python3 fix_session.py sessions
5. 運行: chmod +x start_worker.sh && ./start_worker.sh

## Excel 配置說明

每個 Worker 節點需要一個 Excel 配置文件（${config.node_id}.xlsx），包含以下列：

必需列：
- api_id: Telegram API ID（數字）
- api_hash: Telegram API Hash（32位字符串）
- phone: 電話號碼（用於匹配 session 文件）

可選列（自動填充）：
- username: 用戶名
- name: 昵稱
- user_id: Telegram 數字 ID
- friends: 好友數量
- groups: 群組數量

管理列：
- group: 分組名稱
- remark: 備註
- node: 指定節點
- enabled: 是否啟用（1=啟用，0=禁用）

## 後台運行

### Windows
\`\`\`
start /b pythonw worker_client.py
\`\`\`

### Linux
\`\`\`
nohup ./start_worker.sh > worker.log 2>&1 &
\`\`\`
`)
      }
      
      // 生成 ZIP 並下載
      const content = await zip.generateAsync({ type: "blob" })
      const url = URL.createObjectURL(content)
      const a = document.createElement("a")
      a.href = url
      a.download = `worker-deploy-${config.node_id}.zip`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
      
      toast({ 
        title: "✅ 下載成功",
        description: `worker-deploy-${config.node_id}.zip`
      })
    } catch (error) {
      console.error("ZIP 生成失敗:", error)
      toast({ 
        title: "❌ 下載失敗",
        description: "無法生成 ZIP 文件",
        variant: "destructive"
      })
    } finally {
      setDownloading(false)
    }
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
                <Label htmlFor="node_id" className="flex items-center gap-1">
                  節點 ID *
                  <TooltipProvider>
                    <Tooltip>
                      <TooltipTrigger>
                        <HelpCircle className="h-3.5 w-3.5 text-muted-foreground" />
                      </TooltipTrigger>
                      <TooltipContent className="max-w-xs">
                        <p className="font-medium mb-1">節點 ID 命名建議：</p>
                        <ul className="text-xs space-y-1">
                          <li>• <code>worker_辦公室</code> - 按位置命名</li>
                          <li>• <code>worker_張三電腦</code> - 按使用者命名</li>
                          <li>• <code>worker_aws_01</code> - 按服務器命名</li>
                          <li>• <code>worker_192.168.1.100</code> - 按IP命名</li>
                        </ul>
                        <p className="text-xs mt-2 text-muted-foreground">用於在控制台識別不同電腦</p>
                      </TooltipContent>
                    </Tooltip>
                  </TooltipProvider>
                </Label>
                <div className="flex gap-2">
                  <Input
                    id="node_id"
                    value={config.node_id}
                    onChange={(e) => setConfig({ ...config, node_id: e.target.value })}
                    placeholder="worker_辦公室"
                  />
                  <Button 
                    variant="outline" 
                    size="icon"
                    onClick={() => setConfig({ ...config, node_id: generateNodeId() })}
                    title="隨機生成"
                  >
                    🎲
                  </Button>
                </div>
                <p className="text-xs text-muted-foreground">給這台電腦起個名字，方便識別</p>
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
                <Button onClick={downloadZip} variant="default" size="sm" disabled={downloading}>
                  <Package className="h-4 w-4 mr-2" />
                  {downloading ? "打包中..." : "下載 ZIP 壓縮包"}
                </Button>
              </CardTitle>
              <CardDescription>
                下載壓縮包後解壓，運行對應系統的啟動腳本即可
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
            <CardTitle>📖 使用說明</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* 步驟說明 */}
            <div className="bg-gradient-to-r from-blue-500/10 to-purple-500/10 p-4 rounded-lg">
              <h4 className="font-medium mb-3">🚀 快速開始（3 步完成）</h4>
              <div className="grid gap-3">
                <div className="flex items-start gap-3">
                  <span className="bg-blue-500 text-white rounded-full w-6 h-6 flex items-center justify-center text-sm font-bold flex-shrink-0">1</span>
                  <div>
                    <p className="font-medium">下載並解壓</p>
                    <p className="text-sm text-muted-foreground">點擊「下載 ZIP 壓縮包」，解壓到任意目錄</p>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <span className="bg-blue-500 text-white rounded-full w-6 h-6 flex items-center justify-center text-sm font-bold flex-shrink-0">2</span>
                  <div>
                    <p className="font-medium">放入 Session 文件</p>
                    <p className="text-sm text-muted-foreground">將 Telegram .session 文件放入 <code className="bg-muted px-1 rounded">sessions</code> 目錄</p>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <span className="bg-blue-500 text-white rounded-full w-6 h-6 flex items-center justify-center text-sm font-bold flex-shrink-0">3</span>
                  <div>
                    <p className="font-medium">運行啟動腳本</p>
                    <p className="text-sm text-muted-foreground">
                      Windows: 雙擊 <code className="bg-muted px-1 rounded">start_worker.bat</code><br/>
                      Linux/Mac: 運行 <code className="bg-muted px-1 rounded">./start_worker.sh</code>
                    </p>
                  </div>
                </div>
              </div>
            </div>

            {/* 節點ID說明 */}
            <div className="border-t pt-4">
              <h4 className="font-medium mb-2">❓ 節點 ID 怎麼填</h4>
              <p className="text-sm text-muted-foreground mb-2">
                節點 ID 是用來在控制台識別這台電腦的名字，可以隨意命名：
              </p>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-sm">
                <div className="bg-muted p-2 rounded text-center">
                  <code>worker_辦公室</code>
                </div>
                <div className="bg-muted p-2 rounded text-center">
                  <code>worker_張三</code>
                </div>
                <div className="bg-muted p-2 rounded text-center">
                  <code>worker_aws_01</code>
                </div>
                <div className="bg-muted p-2 rounded text-center">
                  <code>worker_home</code>
                </div>
              </div>
            </div>
            
            {/* 後台運行 */}
            <div className="border-t pt-4">
              <h4 className="font-medium mb-2">🔄 後台運行（可選）</h4>
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

            {/* 壓縮包內容 */}
            <div className="border-t pt-4">
              <h4 className="font-medium mb-2">📁 壓縮包內容</h4>
              <pre className="bg-muted p-3 rounded text-xs">
{`worker-deploy-${config.node_id}/
├── start_worker.bat    # Windows 啟動腳本
├── start_worker.sh     # Linux/Mac 啟動腳本
├── worker_client.py    # Python 客戶端
├── README.md           # 說明文檔
└── sessions/           # 放置 .session 文件
    └── README.txt`}
              </pre>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

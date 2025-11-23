"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { useToast } from "@/hooks/use-toast";
import { Phone, Clock, CheckCircle2, AlertCircle, Shield } from "lucide-react";
import {
  startTelegramRegistration,
  verifyTelegramCode,
  getTelegramRegistrationStatus,
  cancelTelegramRegistration,
  type TelegramRegistrationStatus,
} from "@/lib/api/telegram-registration";
import { getServers, type ServerStatus } from "@/lib/api/servers";

interface Step {
  title: string;
  description: string;
  icon: React.ReactNode;
}

const steps: Step[] = [
  {
    title: "配置信息",
    description: "选择服务器和输入手机号",
    icon: <Phone className="h-4 w-4" />,
  },
  {
    title: "验证码验证",
    description: "输入收到的验证码",
    icon: <Clock className="h-4 w-4" />,
  },
  {
    title: "完成",
    description: "注册完成",
    icon: <CheckCircle2 className="h-4 w-4" />,
  },
];

export default function TelegramRegisterPage() {
  const { toast } = useToast();
  const [servers, setServers] = useState<ServerStatus[]>([]);
  const [loading, setLoading] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);
  const [registrationId, setRegistrationId] = useState<string | null>(null);
  const [status, setStatus] = useState<TelegramRegistrationStatus | null>(null);
  const [riskScore, setRiskScore] = useState<number | null>(null);
  
  // 表单状态
  const [phone, setPhone] = useState("");
  const [nodeId, setNodeId] = useState("");
  const [apiId, setApiId] = useState("");
  const [apiHash, setApiHash] = useState("");
  const [sessionName, setSessionName] = useState("");
  const [useProxy, setUseProxy] = useState(false);
  const [proxyUrl, setProxyUrl] = useState("");
  const [code, setCode] = useState("");
  const [password, setPassword] = useState("");

  // 加载服务器列表
  useEffect(() => {
    const loadServers = async () => {
      try {
        const serverList = await getServers();
        setServers(serverList);
      } catch (error: any) {
        console.error("加载服务器列表失败:", error);
        const errorMessage = error.message || "加载服务器列表失败";
        toast({
          title: "错误",
          description: errorMessage,
          variant: "destructive",
        });
        // 如果是认证错误，可能需要重新登录
        if (errorMessage.includes("认证失败") || errorMessage.includes("401")) {
          // 延迟重定向，让用户看到错误提示
          setTimeout(() => {
            window.location.href = "/login";
          }, 2000);
        }
      }
    };
    loadServers();
  }, [toast]);

  // 轮询注册状态
  useEffect(() => {
    if (!registrationId || currentStep === 2) return;

    const interval = setInterval(async () => {
      try {
        const data = await getTelegramRegistrationStatus(registrationId);
        setStatus(data);
        
        if (data.status === "completed") {
          toast({
            title: "成功",
            description: "注册成功！",
          });
          setCurrentStep(2);
          clearInterval(interval);
        } else if (data.status === "failed") {
          toast({
            title: "失败",
            description: data.error_message || "注册失败",
            variant: "destructive",
          });
          clearInterval(interval);
        } else if (data.status === "code_sent") {
          // 确保切换到验证码输入步骤
          setCurrentStep(1);
          // 更新状态（包括 expires_at）
          setStatus(data);
          // 如果是模拟模式，显示验证码提示
          if ((data as any).mock_mode && (data as any).mock_code) {
            toast({
              title: "模拟模式",
              description: `验证码: ${(data as any).mock_code}`,
            });
          }
        }
      } catch (error) {
        console.error("获取状态失败:", error);
      }
    }, 2000);

    return () => clearInterval(interval);
  }, [registrationId, currentStep, toast]);


  // 从手机号中提取国家代码
  const extractCountryCode = (phoneNumber: string): string => {
    // 如果手机号以 + 开头，提取国家代码（通常是 1-4 位数字）
    if (phoneNumber.startsWith("+")) {
      // 匹配常见的国家代码格式（1-4位数字）
      const match = phoneNumber.match(/^\+(\d{1,4})/);
      if (match) {
        return `+${match[1]}`;
      }
    }
    // 如果没有 + 或无法提取，返回默认值
    return "+1";
  };

  const handleStart = async () => {
    if (!phone || !nodeId) {
      toast({
        title: "错误",
        description: "请填写手机号和选择服务器",
        variant: "destructive",
      });
      return;
    }

    // 验证手机号格式（必须包含国家代码）
    if (!phone.startsWith("+")) {
      toast({
        title: "错误",
        description: "手机号必须包含国家代码，例如: +1234567890",
        variant: "destructive",
      });
      return;
    }

    setLoading(true);
    try {
      // 从手机号中提取国家代码
      const countryCode = extractCountryCode(phone);
      
      const data = await startTelegramRegistration({
        phone,
        country_code: countryCode,
        node_id: nodeId,
        api_id: apiId ? parseInt(apiId) : undefined,
        api_hash: apiHash || undefined,
        session_name: sessionName || undefined,
        use_proxy: useProxy,
        proxy_url: useProxy ? proxyUrl : undefined,
      });
      
      setRegistrationId(data.registration_id);
      setStatus(data);
      setRiskScore(data.risk_score || null);
      
      // 无论状态如何，都立即切换到验证码输入步骤
      // 因为验证码发送是异步的，可能需要等待
      setCurrentStep(1);
      
      // 如果验证码已发送，显示提示
      if (data.status === "code_sent") {
        // 如果是模拟模式，显示验证码提示
        if (data.mock_mode && data.mock_code) {
          toast({
            title: "模拟模式",
            description: `验证码: ${data.mock_code}`,
          });
        } else {
          // 检查是否切换了服务器
          const serverSwitched = (data as any).server_switched;
          toast({
            title: serverSwitched ? "⚠️ 已切换到新服务器" : "验证码已发送",
            description: serverSwitched 
              ? `已切换到新服务器，新的验证码已发送到 ${phone}，请使用新收到的验证码（旧服务器的验证码已失效）`
              : `验证码已发送到 ${phone}，请查收`,
            variant: serverSwitched ? "default" : "default",
          });
        }
      } else {
        // 如果状态是 pending，说明验证码正在发送
        toast({
          title: "正在发送验证码",
          description: `正在向 ${phone} 发送验证码，请稍候...`,
        });
      }
    } catch (error: any) {
      toast({
        title: "错误",
        description: error.message || "启动注册失败",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const handleVerify = async () => {
    if (!registrationId || !code) {
      toast({
        title: "错误",
        description: "请输入验证码",
        variant: "destructive",
      });
      return;
    }
    
    setLoading(true);
    try {
      const data = await verifyTelegramCode({
        registration_id: registrationId,
        code,
        password: password || undefined,
      });
      
      setStatus(data);
      
      if (data.status === "completed") {
        setCurrentStep(2);
      } else if (data.status === "password_required") {
        toast({
          title: "提示",
          description: "需要输入两步验证密码",
        });
      } else if (data.status === "failed") {
        toast({
          title: "失败",
          description: data.error_message || "验证失败",
          variant: "destructive",
        });
      }
    } catch (error: any) {
      toast({
        title: "错误",
        description: error.message || "验证失败",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setCurrentStep(0);
    setRegistrationId(null);
    setStatus(null);
    setRiskScore(null);
    setPhone("");
    setNodeId("");
    setApiId("");
    setApiHash("");
    setSessionName("");
    setUseProxy(false);
    setProxyUrl("");
    setCode("");
    setPassword("");
  };

  const getRiskLevel = (score: number | null) => {
    if (score === null) return null;
    if (score <= 25) return { level: "低风险", color: "text-green-600" };
    if (score <= 50) return { level: "中风险", color: "text-yellow-600" };
    if (score <= 75) return { level: "高风险", color: "text-orange-600" };
    return { level: "极高风险", color: "text-red-600" };
  };

  const riskInfo = getRiskLevel(riskScore);

  return (
    <div className="container mx-auto py-6 max-w-4xl">
      <Card>
        <CardHeader>
          <CardTitle>Telegram API 注册</CardTitle>
          <CardDescription>注册新的 Telegram 账号并生成 Session 文件</CardDescription>
        </CardHeader>
        <CardContent>
          {/* 步骤指示器 */}
          <div className="flex items-center justify-between mb-8">
            {steps.map((step, index) => (
              <div key={index} className="flex items-center flex-1">
                <div className="flex flex-col items-center flex-1">
                  <div
                    className={`w-10 h-10 rounded-full flex items-center justify-center ${
                      index <= currentStep
                        ? "bg-primary text-primary-foreground"
                        : "bg-muted text-muted-foreground"
                    }`}
                  >
                    {step.icon}
                  </div>
                  <div className="mt-2 text-sm text-center">
                    <div className="font-medium">{step.title}</div>
                    <div className="text-xs text-muted-foreground">{step.description}</div>
                  </div>
                </div>
                {index < steps.length - 1 && (
                  <div
                    className={`h-0.5 flex-1 mx-2 ${
                      index < currentStep ? "bg-primary" : "bg-muted"
                    }`}
                  />
                )}
              </div>
            ))}
          </div>

          {/* 风险提示 */}
          {riskInfo && currentStep < 2 && (
            <Alert className="mb-6">
              <Shield className="h-4 w-4" />
              <AlertTitle>风险评分</AlertTitle>
              <AlertDescription>
                当前风险评分: <span className={riskInfo.color}>{riskScore} ({riskInfo.level})</span>
              </AlertDescription>
            </Alert>
          )}

          {/* 步骤 0: 配置信息 */}
          {currentStep === 0 && (
            <div className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="phone">手机号（必须包含国家代码）</Label>
                <Input
                  id="phone"
                  type="tel"
                  placeholder="例如: +1234567890 或 +8613800138000"
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                />
                <p className="text-sm text-muted-foreground">
                  请输入完整的手机号，包括国家代码（以 + 开头），例如：+1 (美国/加拿大)、+86 (中国)、+44 (英国) 等
                </p>
              </div>

              <div className="space-y-2">
                <Label htmlFor="node_id">选择服务器</Label>
                <Select value={nodeId} onValueChange={setNodeId}>
                  <SelectTrigger>
                    <SelectValue placeholder="选择服务器" />
                  </SelectTrigger>
                  <SelectContent>
                    {servers.map((server) => (
                      <SelectItem key={server.node_id} value={server.node_id}>
                        {server.node_id} ({server.host}) - {server.status === "online" ? "在线" : "离线"}
                        {server.accounts_count !== undefined && ` (${server.accounts_count}/${server.max_accounts || 0})`}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-4 border-t pt-4">
                <Label>高级选项</Label>
                <div className="space-y-2">
                  <Input
                    placeholder="API ID（可选，使用服务器默认配置）"
                    value={apiId}
                    onChange={(e) => setApiId(e.target.value)}
                  />
                  <Input
                    type="password"
                    placeholder="API Hash（可选，使用服务器默认配置）"
                    value={apiHash}
                    onChange={(e) => setApiHash(e.target.value)}
                  />
                  <Input
                    placeholder="Session名称（可选，默认使用手机号）"
                    value={sessionName}
                    onChange={(e) => setSessionName(e.target.value)}
                  />
                  <div className="flex items-center space-x-2">
                    <Switch
                      id="use_proxy"
                      checked={useProxy}
                      onCheckedChange={setUseProxy}
                    />
                    <Label htmlFor="use_proxy">使用代理</Label>
                  </div>
                  {useProxy && (
                    <Input
                      placeholder="例如: socks5://127.0.0.1:1080 或 http://user:pass@proxy.com:8080"
                      value={proxyUrl}
                      onChange={(e) => setProxyUrl(e.target.value)}
                    />
                  )}
                </div>
              </div>

              <Button onClick={handleStart} disabled={loading} className="w-full" size="lg">
                {loading ? "处理中..." : "开始注册"}
              </Button>
            </div>
          )}

          {/* 步骤 1: 验证码验证 */}
          {currentStep === 1 && (
            <div className="space-y-4">
              <div className="text-center mb-4">
                <h3 className="text-lg font-semibold">验证码验证</h3>
                <p className="text-sm text-muted-foreground">请输入收到的验证码</p>
              </div>

              {/* 模拟模式提示 */}
              {status?.mock_mode && status?.mock_code && (
                <Alert>
                  <AlertCircle className="h-4 w-4" />
                  <AlertTitle>模拟模式</AlertTitle>
                  <AlertDescription>
                    当前为模拟模式，验证码: <strong>{status.mock_code}</strong>（仅用于测试）
                  </AlertDescription>
                </Alert>
              )}
              
              {riskInfo && (
                <Card>
                  <CardContent className="pt-6">
                    <div className="flex items-center space-x-2">
                      <Shield className="h-4 w-4" />
                      <div>
                        <div className="text-sm text-muted-foreground">风险评分</div>
                        <div className={`text-2xl font-bold ${riskInfo.color}`}>
                          {riskScore} ({riskInfo.level})
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )}

              {status?.error_message && (
                <Alert variant="destructive">
                  <AlertCircle className="h-4 w-4" />
                  <AlertTitle>错误</AlertTitle>
                  <AlertDescription>{status.error_message}</AlertDescription>
                </Alert>
              )}

              {/* 验证码输入框 - 突出显示 */}
              <Card className="border-2 border-primary">
                <CardContent className="pt-6">
                  <div className="space-y-2">
                    <Label htmlFor="code" className="text-base font-semibold">验证码</Label>
                    <Input
                      id="code"
                      type="text"
                      placeholder="请输入收到的验证码（6位数字）"
                      maxLength={6}
                      value={code}
                      onChange={(e) => setCode(e.target.value.replace(/\D/g, ''))}
                      className="text-center text-3xl tracking-widest font-bold h-16"
                      autoFocus
                    />
                    <p className="text-sm text-muted-foreground text-center">
                      验证码已发送到 {phone}，请查收短信或 Telegram 应用
                    </p>
                  </div>
                </CardContent>
              </Card>

              {code.length >= 5 && status?.status === "password_required" && (
                <div className="space-y-2">
                  <Label htmlFor="password">两步验证密码</Label>
                  <Input
                    id="password"
                    type="password"
                    placeholder="请输入两步验证密码"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                  />
                </div>
              )}

              <div className="flex space-x-2">
                <Button onClick={handleVerify} disabled={loading} className="flex-1" size="lg">
                  {loading ? "验证中..." : "验证"}
                </Button>
                <Button onClick={handleReset} variant="outline" size="lg">
                  重新开始
                </Button>
              </div>
            </div>
          )}

          {/* 步骤 2: 完成 */}
          {currentStep === 2 && status && (
            <div className="text-center space-y-4">
              <CheckCircle2 className="h-16 w-16 text-green-600 mx-auto" />
              <div className="text-2xl font-bold">注册成功！</div>
              <div className="text-muted-foreground">
                Session文件已保存到服务器的 sessions 目录
              </div>
              {status.session_file && (
                <Card>
                  <CardContent className="pt-6">
                    <div className="text-left space-y-2">
                      <div><strong>Session名称:</strong> {status.session_file.session_name}</div>
                      <div><strong>服务器节点:</strong> {status.session_file.server_node_id}</div>
                      <div><strong>文件大小:</strong> {status.session_file.file_size} 字节</div>
                    </div>
                  </CardContent>
                </Card>
              )}
              <Button onClick={handleReset} size="lg">
                注册新的账号
              </Button>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}


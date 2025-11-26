"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Server, Play, Square, RotateCw, RefreshCw, AlertCircle, CheckCircle2, XCircle, FileText, Users, Trash2, Plus, MoreVertical, CheckSquare } from "lucide-react";
import { getServers, getServerLogs, serverAction, scanServerAccounts, deleteServerAccount, batchDeleteServerAccounts, allocateAccountToServer, type ServerStatus, type ServerLogEntry, type ServerAccount, type ScanServerAccountsResponse } from "@/lib/api/servers";
import { getScripts } from "@/lib/api/group-ai";
import { useToast } from "@/hooks/use-toast";
import { PermissionGuard } from "@/components/permissions/permission-guard";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Checkbox } from "@/components/ui/checkbox";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger, DropdownMenuSeparator } from "@/components/ui/dropdown-menu";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export default function ServersPage() {
  const [servers, setServers] = useState<ServerStatus[]>([]);
  const [loading, setLoading] = useState(false); // 改为false，初始不显示loading
  const [selectedServer, setSelectedServer] = useState<string | null>(null);
  const [logs, setLogs] = useState<ServerLogEntry[]>([]);
  const [logsLoading, setLogsLoading] = useState(false);
  const [actionLoading, setActionLoading] = useState<Record<string, boolean>>({});
  const [dialogOpen, setDialogOpen] = useState<Record<string, boolean>>({});
  const [accountDialogOpen, setAccountDialogOpen] = useState<Record<string, boolean>>({});
  const [serverAccounts, setServerAccounts] = useState<Record<string, ServerAccount[]>>({});
  const [accountsLoading, setAccountsLoading] = useState<Record<string, boolean>>({});
  const [selectedAccounts, setSelectedAccounts] = useState<Record<string, Set<string>>>({});
  const [addAccountDialogOpen, setAddAccountDialogOpen] = useState<Record<string, boolean>>({});
  const [newAccountId, setNewAccountId] = useState("");
  const [newAccountSessionFile, setNewAccountSessionFile] = useState("");
  const [newAccountScriptId, setNewAccountScriptId] = useState("");
  const [availableScripts, setAvailableScripts] = useState<Array<{ script_id: string; name: string }>>([]);
  const { toast } = useToast();

  const fetchServers = async (showLoading = false) => {
    try {
      if (showLoading) {
        setLoading(true);
      }
      const data = await getServers();
      setServers(data);
    } catch (error) {
      console.error("獲取服務器列表失敗:", error);
      toast({
        title: "錯誤",
        description: "無法獲取服務器列表",
        variant: "destructive",
      });
    } finally {
      if (showLoading) {
        setLoading(false);
      }
    }
  };

  const fetchLogs = async (nodeId: string) => {
    try {
      setLogsLoading(true);
      const data = await getServerLogs(nodeId, 200);
      setLogs(data);
    } catch (error) {
      console.error("獲取日誌失敗:", error);
      toast({
        title: "錯誤",
        description: "無法獲取服務器日誌",
        variant: "destructive",
      });
    } finally {
      setLogsLoading(false);
    }
  };

  const handleAction = async (nodeId: string, action: "start" | "stop" | "restart") => {
    // 立即显示提示和更新UI（乐观更新）
    const actionKey = `${nodeId}-${action}`;
    setActionLoading(prev => ({ ...prev, [actionKey]: true }));
    
    // 立即更新服务器状态（乐观更新）
    setServers(prev => prev.map(server => {
      if (server.node_id === nodeId) {
        let newStatus: "online" | "offline" | "error" = server.status;
        if (action === "start") {
          newStatus = "online";
        } else if (action === "stop") {
          newStatus = "offline";
        }
        return { ...server, status: newStatus };
      }
      return server;
    }));
    
    // 立即显示成功提示
    toast({
      title: "操作中",
      description: `正在${action === "start" ? "啟動" : action === "stop" ? "停止" : "重啟"}服務器...`,
    });
    
    try {
      const result = await serverAction(nodeId, action);
      if (result.success) {
        // 更新提示为成功
        toast({
          title: "成功",
          description: result.message,
        });
        // 立即刷新列表获取真实状态
        setTimeout(() => fetchServers(false), 1000);
      } else {
        // 回滚状态
        setServers(prev => prev.map(server => {
          if (server.node_id === nodeId) {
            return { ...server, status: "error" };
          }
          return server;
        }));
        toast({
          title: "失敗",
          description: result.message,
          variant: "destructive",
        });
      }
    } catch (error: any) {
      // 回滚状态
      setServers(prev => prev.map(server => {
        if (server.node_id === nodeId) {
          return { ...server, status: "error" };
        }
        return server;
      }));
      toast({
        title: "錯誤",
        description: error.message || "操作失敗",
        variant: "destructive",
      });
    } finally {
      setActionLoading(prev => ({ ...prev, [actionKey]: false }));
    }
  };

  useEffect(() => {
    // 初始加载时静默加载，不显示loading
    fetchServers(false);
    // 每30秒自動刷新（静默）
    const interval = setInterval(() => fetchServers(false), 30000);
    
    // 加载剧本列表
    const loadScripts = async () => {
      try {
        const scripts = await getScripts();
        setAvailableScripts(scripts.map(s => ({ script_id: s.script_id, name: s.name })));
      } catch (error) {
        console.error("加载剧本列表失败:", error);
      }
    };
    loadScripts();
    
    return () => clearInterval(interval);
  }, []);

  const fetchServerAccounts = async (serverId: string) => {
    try {
      setAccountsLoading(prev => ({ ...prev, [serverId]: true }));
      const data = await scanServerAccounts(serverId);
      console.log("獲取到的服務器賬號數據:", data);
      console.log("數據類型:", Array.isArray(data) ? "數組" : "對象");
      console.log("數據內容:", JSON.stringify(data, null, 2));
      
      // 處理返回格式：API總是返回數組
      let accounts: ServerAccount[] = [];
      
      if (Array.isArray(data)) {
        // 如果是數組，找到對應服務器的數據
        if (data.length > 0) {
          const serverData = data.find(item => item && item.server_id === serverId);
          if (serverData && serverData.accounts) {
            accounts = Array.isArray(serverData.accounts) ? serverData.accounts : [];
            console.log(`找到服務器 ${serverId} 的 ${accounts.length} 個賬號`);
          } else if (data.length === 1 && data[0]) {
            // 如果只有一個結果且沒有指定server_id，可能是單個服務器掃描結果
            const firstResult = data[0];
            if (firstResult.server_id === serverId || !serverId) {
              accounts = Array.isArray(firstResult.accounts) ? firstResult.accounts : [];
              console.log(`使用第一個結果，找到 ${accounts.length} 個賬號`);
            }
          } else {
            console.warn(`未找到服務器 ${serverId} 的數據，數組長度: ${data.length}`);
          }
        } else {
          console.warn("返回的數據是空數組");
        }
      } else if (data && typeof data === 'object' && 'server_id' in data) {
        // 如果是單個對象（不應該發生，但為了兼容性保留）
        const objData = data as { server_id: string; accounts?: ServerAccount[] };
        if (objData.server_id === serverId || !serverId) {
          accounts = Array.isArray(objData.accounts) ? objData.accounts : [];
          console.log(`使用單個對象結果，找到 ${accounts.length} 個賬號`);
        }
      } else {
        console.error("返回的數據格式不正確:", typeof data, data);
      }
      
      console.log("解析後的賬號列表:", accounts.map(acc => ({ account_id: acc.account_id, session_file: acc.session_file })));
      setServerAccounts(prev => ({ ...prev, [serverId]: accounts }));
    } catch (error: any) {
      console.error("獲取服務器賬號失敗:", error);
      toast({
        title: "錯誤",
        description: error.message || "無法獲取服務器賬號列表",
        variant: "destructive",
      });
      // 設置為空數組，避免顯示錯誤狀態
      setServerAccounts(prev => ({ ...prev, [serverId]: [] }));
    } finally {
      setAccountsLoading(prev => ({ ...prev, [serverId]: false }));
    }
  };

  const handleDeleteAccount = async (serverId: string, accountId: string) => {
    try {
      await deleteServerAccount(serverId, accountId);
      toast({
        title: "成功",
        description: `已刪除賬號 ${accountId}`,
      });
      // 刷新賬號列表和服務器列表
      fetchServerAccounts(serverId);
      fetchServers(false);
    } catch (error: any) {
      toast({
        title: "錯誤",
        description: error.message || "刪除賬號失敗",
        variant: "destructive",
      });
    }
  };

  const handleBatchDelete = async (serverId: string) => {
    const selected = selectedAccounts[serverId] || new Set();
    if (selected.size === 0) {
      toast({
        title: "提示",
        description: "請選擇要刪除的賬號",
        variant: "destructive",
      });
      return;
    }

    if (!confirm(`確定要刪除 ${selected.size} 個賬號嗎？此操作不可恢復！`)) {
      return;
    }

    try {
      const result = await batchDeleteServerAccounts(serverId, Array.from(selected));
      toast({
        title: result.success ? "成功" : "部分失敗",
        description: result.message,
        variant: result.success ? "default" : "destructive",
      });
      // 清除選中狀態
      setSelectedAccounts(prev => ({ ...prev, [serverId]: new Set() }));
      // 刷新列表
      fetchServerAccounts(serverId);
      fetchServers(false);
    } catch (error: any) {
      toast({
        title: "錯誤",
        description: error.message || "批量刪除失敗",
        variant: "destructive",
      });
    }
  };

  const handleAddAccount = async (serverId: string) => {
    if (!newAccountId || !newAccountSessionFile) {
      toast({
        title: "錯誤",
        description: "請填寫賬號ID和Session文件路徑",
        variant: "destructive",
      });
      return;
    }

    try {
      const result = await allocateAccountToServer(newAccountId, newAccountSessionFile, serverId, newAccountScriptId || undefined);
      if (result.success) {
        toast({
          title: "成功",
          description: result.message,
        });
        // 重置表單
        setNewAccountId("");
        setNewAccountSessionFile("");
        setNewAccountScriptId("");
        setAddAccountDialogOpen(prev => ({ ...prev, [serverId]: false }));
        // 刷新列表
        fetchServerAccounts(serverId);
        fetchServers(false);
      } else {
        toast({
          title: "失敗",
          description: result.message,
          variant: "destructive",
        });
      }
    } catch (error: any) {
      toast({
        title: "錯誤",
        description: error.message || "添加賬號失敗",
        variant: "destructive",
      });
    }
  };

  const toggleAccountSelection = (serverId: string, accountId: string) => {
    setSelectedAccounts(prev => {
      const current = prev[serverId] || new Set();
      const newSet = new Set(current);
      if (newSet.has(accountId)) {
        newSet.delete(accountId);
      } else {
        newSet.add(accountId);
      }
      return { ...prev, [serverId]: newSet };
    });
  };

  const toggleSelectAll = (serverId: string) => {
    const accounts = serverAccounts[serverId] || [];
    const current = selectedAccounts[serverId] || new Set();
    const allSelected = accounts.length > 0 && accounts.every(acc => current.has(acc.account_id));
    
    setSelectedAccounts(prev => {
      if (allSelected) {
        return { ...prev, [serverId]: new Set() };
      } else {
        return { ...prev, [serverId]: new Set(accounts.map(acc => acc.account_id)) };
      }
    });
  };

  useEffect(() => {
    if (selectedServer) {
      // 立即加载日志
      fetchLogs(selectedServer);
      // 每10秒刷新日誌（仅在对话框打开时）
      const interval = setInterval(() => {
        if (dialogOpen[selectedServer]) {
          fetchLogs(selectedServer);
        }
      }, 10000);
      return () => clearInterval(interval);
    }
  }, [selectedServer, dialogOpen]);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "online":
        return <CheckCircle2 className="h-5 w-5 text-green-500" />;
      case "offline":
        return <XCircle className="h-5 w-5 text-gray-400" />;
      case "error":
        return <AlertCircle className="h-5 w-5 text-red-500" />;
      default:
        return <Server className="h-5 w-5 text-gray-400" />;
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "online":
        return <Badge className="bg-green-500">在線</Badge>;
      case "offline":
        return <Badge variant="secondary">離線</Badge>;
      case "error":
        return <Badge variant="destructive">錯誤</Badge>;
      default:
        return <Badge variant="outline">未知</Badge>;
    }
  };

  return (
    <PermissionGuard permission="server:view" fallback={
      <div className="container mx-auto py-6">
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>您沒有權限查看服務器管理</AlertDescription>
        </Alert>
      </div>
    }>
      <div className="container mx-auto py-6 space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold">服務器管理</h1>
            <p className="text-muted-foreground">管理和監控遠程服務器節點</p>
          </div>
          <PermissionGuard permission="server:view">
            <Button onClick={() => fetchServers(true)} variant="outline" size="sm">
              <RefreshCw className="h-4 w-4 mr-2" />
              刷新
            </Button>
          </PermissionGuard>
        </div>

      <Card>
        <CardHeader>
          <CardTitle>服務器列表</CardTitle>
          <CardDescription>所有已部署的服務器節點狀態</CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="text-center py-8">載入中...</div>
          ) : servers.length === 0 && !loading ? (
            <div className="text-center py-8 text-muted-foreground">
              <Server className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p>暫無服務器</p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>節點ID</TableHead>
                  <TableHead>主機地址</TableHead>
                  <TableHead>狀態</TableHead>
                  <TableHead>帳號數</TableHead>
                  <TableHead>服務狀態</TableHead>
                  <TableHead>操作</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {servers.map((server) => (
                  <TableRow key={server.node_id}>
                    <TableCell className="font-medium">{server.node_id}</TableCell>
                    <TableCell>{server.host}:{server.port}</TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        {getStatusIcon(server.status)}
                        {getStatusBadge(server.status)}
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <span className={server.accounts_count > server.max_accounts ? "text-red-500 font-semibold" : ""}>
                          {server.accounts_count} / {server.max_accounts}
                        </span>
                        {server.accounts_count > server.max_accounts && (
                          <Badge variant="destructive" className="text-xs">超限</Badge>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      <span className="text-sm text-muted-foreground">
                        {server.service_status || "未知"}
                      </span>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <PermissionGuard permission="server:control">
                          <Button
                            size="sm"
                            variant={server.status === "online" ? "secondary" : "default"}
                            onClick={() => handleAction(server.node_id, "start")}
                            disabled={server.status === "online" || actionLoading[`${server.node_id}-start`]}
                            className={server.status === "online" ? "opacity-50" : ""}
                          >
                            <Play className="h-3 w-3 mr-1" />
                            {actionLoading[`${server.node_id}-start`] ? "啟動中..." : "啟動"}
                          </Button>
                          <Button
                            size="sm"
                            variant={server.status === "offline" ? "secondary" : "default"}
                            onClick={() => handleAction(server.node_id, "stop")}
                            disabled={server.status === "offline" || actionLoading[`${server.node_id}-stop`]}
                            className={server.status === "offline" ? "opacity-50" : ""}
                          >
                            <Square className="h-3 w-3 mr-1" />
                            {actionLoading[`${server.node_id}-stop`] ? "停止中..." : "停止"}
                          </Button>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => handleAction(server.node_id, "restart")}
                            disabled={actionLoading[`${server.node_id}-restart`]}
                          >
                            <RotateCw className={`h-3 w-3 mr-1 ${actionLoading[`${server.node_id}-restart`] ? "animate-spin" : ""}`} />
                            {actionLoading[`${server.node_id}-restart`] ? "重啟中..." : "重啟"}
                          </Button>
                        </PermissionGuard>
                        <Dialog 
                          open={dialogOpen[server.node_id] || false}
                          onOpenChange={(open) => {
                            setDialogOpen(prev => ({ ...prev, [server.node_id]: open }));
                            if (open) {
                              setSelectedServer(server.node_id);
                              // 立即开始加载日志
                              fetchLogs(server.node_id);
                            } else {
                              setSelectedServer(null);
                            }
                          }}
                        >
                          <DialogTrigger asChild>
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => {
                                setDialogOpen(prev => ({ ...prev, [server.node_id]: true }));
                                setSelectedServer(server.node_id);
                                // 立即开始加载日志
                                fetchLogs(server.node_id);
                              }}
                            >
                              <FileText className="h-3 w-3 mr-1" />
                              日誌
                            </Button>
                          </DialogTrigger>
                          <DialogContent className="max-w-4xl max-h-[80vh]">
                            <DialogHeader>
                              <DialogTitle>服務器日誌 - {server.node_id}</DialogTitle>
                              <DialogDescription>{server.host}</DialogDescription>
                            </DialogHeader>
                            <ScrollArea className="h-[60vh]">
                              {logsLoading && selectedServer === server.node_id ? (
                                <div className="text-center py-8">載入日誌中...</div>
                              ) : logs.length === 0 && selectedServer === server.node_id ? (
                                <div className="text-center py-8 text-muted-foreground">暫無日誌</div>
                              ) : selectedServer === server.node_id ? (
                                <div className="space-y-1 font-mono text-sm">
                                  {logs.map((log, index) => (
                                    <div
                                      key={index}
                                      className={`p-2 rounded ${
                                        log.level === "ERROR" || log.level === "error"
                                          ? "bg-red-50 text-red-900 dark:bg-red-900/20 dark:text-red-400"
                                          : log.level === "WARNING" || log.level === "warning"
                                          ? "bg-yellow-50 text-yellow-900 dark:bg-yellow-900/20 dark:text-yellow-400"
                                          : "bg-gray-50 dark:bg-gray-800"
                                      }`}
                                    >
                                      {log.timestamp && (
                                        <span className="text-muted-foreground mr-2">
                                          {log.timestamp}
                                        </span>
                                      )}
                                      <span className="font-semibold mr-2">[{log.level}]</span>
                                      {log.message}
                                    </div>
                                  ))}
                                </div>
                              ) : (
                                <div className="text-center py-8 text-muted-foreground">載入中...</div>
                              )}
                            </ScrollArea>
                          </DialogContent>
                        </Dialog>
                        <Dialog
                          open={accountDialogOpen[server.node_id] || false}
                          onOpenChange={(open) => {
                            setAccountDialogOpen(prev => ({ ...prev, [server.node_id]: open }));
                            if (open) {
                              fetchServerAccounts(server.node_id);
                            }
                          }}
                        >
                          <DialogTrigger asChild>
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => {
                                setAccountDialogOpen(prev => ({ ...prev, [server.node_id]: true }));
                                fetchServerAccounts(server.node_id);
                              }}
                            >
                              <Users className="h-3 w-3 mr-1" />
                              賬號管理
                            </Button>
                          </DialogTrigger>
                          <DialogContent className="max-w-4xl max-h-[80vh]">
                            <DialogHeader>
                              <DialogTitle>服務器賬號管理 - {server.node_id}</DialogTitle>
                              <DialogDescription>
                                {server.host}:{server.port} | 賬號數: {server.accounts_count} / {server.max_accounts}
                              </DialogDescription>
                            </DialogHeader>
                            <div className="space-y-4">
                              <div className="flex items-center justify-between">
                                <div className="flex items-center gap-2">
                                  <Button
                                    size="sm"
                                    variant="outline"
                                    onClick={() => toggleSelectAll(server.node_id)}
                                  >
                                    <CheckSquare className="h-4 w-4 mr-1" />
                                    {(serverAccounts[server.node_id] || []).length > 0 && 
                                     (selectedAccounts[server.node_id] || new Set()).size === (serverAccounts[server.node_id] || []).length
                                      ? "取消全選" : "全選"}
                                  </Button>
                                  {(selectedAccounts[server.node_id] || new Set()).size > 0 && (
                                    <Button
                                      size="sm"
                                      variant="destructive"
                                      onClick={() => handleBatchDelete(server.node_id)}
                                    >
                                      <Trash2 className="h-4 w-4 mr-1" />
                                      批量刪除 ({(selectedAccounts[server.node_id] || new Set()).size})
                                    </Button>
                                  )}
                                </div>
                                <div className="flex items-center gap-2">
                                  <Button
                                    size="sm"
                                    variant="outline"
                                    onClick={() => fetchServerAccounts(server.node_id)}
                                    disabled={accountsLoading[server.node_id]}
                                  >
                                    <RefreshCw className={`h-4 w-4 mr-1 ${accountsLoading[server.node_id] ? "animate-spin" : ""}`} />
                                    刷新
                                  </Button>
                                  <Dialog
                                    open={addAccountDialogOpen[server.node_id] || false}
                                    onOpenChange={(open) => setAddAccountDialogOpen(prev => ({ ...prev, [server.node_id]: open }))}
                                  >
                                    <DialogTrigger asChild>
                                      <Button
                                        size="sm"
                                        disabled={server.accounts_count >= server.max_accounts}
                                      >
                                        <Plus className="h-4 w-4 mr-1" />
                                        添加賬號
                                      </Button>
                                    </DialogTrigger>
                                    <DialogContent>
                                      <DialogHeader>
                                        <DialogTitle>添加賬號到 {server.node_id}</DialogTitle>
                                        <DialogDescription>
                                          將賬號分配到當前服務器
                                        </DialogDescription>
                                      </DialogHeader>
                                      <div className="space-y-4">
                                        <div>
                                          <Label htmlFor="account-id">賬號ID</Label>
                                          <Input
                                            id="account-id"
                                            value={newAccountId}
                                            onChange={(e) => setNewAccountId(e.target.value)}
                                            placeholder="例如: 639277356598"
                                          />
                                        </div>
                                        <div>
                                          <Label htmlFor="session-file">Session文件路徑</Label>
                                          <Input
                                            id="session-file"
                                            value={newAccountSessionFile}
                                            onChange={(e) => setNewAccountSessionFile(e.target.value)}
                                            placeholder="例如: sessions/639277356598.session"
                                          />
                                        </div>
                                        <div>
                                          <Label htmlFor="script-id">劇本 (可選)</Label>
                                          <Select
                                            value={newAccountScriptId}
                                            onValueChange={setNewAccountScriptId}
                                          >
                                            <SelectTrigger>
                                              <SelectValue placeholder="選擇劇本" />
                                            </SelectTrigger>
                                            <SelectContent>
                                              <SelectItem value="">無</SelectItem>
                                              {availableScripts.map((script) => (
                                                <SelectItem key={script.script_id} value={script.script_id}>
                                                  {script.name} ({script.script_id})
                                                </SelectItem>
                                              ))}
                                            </SelectContent>
                                          </Select>
                                        </div>
                                        <div className="flex justify-end gap-2">
                                          <Button
                                            variant="outline"
                                            onClick={() => setAddAccountDialogOpen(prev => ({ ...prev, [server.node_id]: false }))}
                                          >
                                            取消
                                          </Button>
                                          <Button
                                            onClick={() => handleAddAccount(server.node_id)}
                                            disabled={!newAccountId || !newAccountSessionFile}
                                          >
                                            添加
                                          </Button>
                                        </div>
                                      </div>
                                    </DialogContent>
                                  </Dialog>
                                </div>
                              </div>
                              <ScrollArea className="h-[50vh]">
                                {accountsLoading[server.node_id] ? (
                                  <div className="text-center py-8">載入中...</div>
                                ) : (serverAccounts[server.node_id] || []).length === 0 ? (
                                  <div className="text-center py-8 text-muted-foreground">
                                    暫無賬號
                                  </div>
                                ) : (
                                  <Table>
                                    <TableHeader>
                                      <TableRow>
                                        <TableHead className="w-12">
                                          <Checkbox
                                            checked={(serverAccounts[server.node_id] || []).length > 0 && 
                                                     (serverAccounts[server.node_id] || []).every(acc => 
                                                       (selectedAccounts[server.node_id] || new Set()).has(acc.account_id)
                                                     )}
                                            onCheckedChange={() => toggleSelectAll(server.node_id)}
                                          />
                                        </TableHead>
                                        <TableHead>賬號ID</TableHead>
                                        <TableHead>Session文件</TableHead>
                                        <TableHead>文件大小</TableHead>
                                        <TableHead>修改時間</TableHead>
                                        <TableHead>操作</TableHead>
                                      </TableRow>
                                    </TableHeader>
                                    <TableBody>
                                      {(serverAccounts[server.node_id] || []).map((account) => (
                                        <TableRow key={account.account_id}>
                                          <TableCell>
                                            <Checkbox
                                              checked={(selectedAccounts[server.node_id] || new Set()).has(account.account_id)}
                                              onCheckedChange={() => toggleAccountSelection(server.node_id, account.account_id)}
                                            />
                                          </TableCell>
                                          <TableCell className="font-medium">{account.account_id}</TableCell>
                                          <TableCell className="text-sm text-muted-foreground">
                                            {account.session_file}
                                          </TableCell>
                                          <TableCell>
                                            {(account.file_size / 1024).toFixed(2)} KB
                                          </TableCell>
                                          <TableCell>
                                            {account.modified_time ? new Date(account.modified_time).toLocaleString() : "-"}
                                          </TableCell>
                                          <TableCell>
                                            <Button
                                              size="sm"
                                              variant="destructive"
                                              onClick={() => {
                                                if (confirm(`確定要刪除賬號 ${account.account_id} 嗎？`)) {
                                                  handleDeleteAccount(server.node_id, account.account_id);
                                                }
                                              }}
                                            >
                                              <Trash2 className="h-3 w-3 mr-1" />
                                              刪除
                                            </Button>
                                          </TableCell>
                                        </TableRow>
                                      ))}
                                    </TableBody>
                                  </Table>
                                )}
                              </ScrollArea>
                            </div>
                          </DialogContent>
                        </Dialog>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
      </div>
    </PermissionGuard>
  );
}


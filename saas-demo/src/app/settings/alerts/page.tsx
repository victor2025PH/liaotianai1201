"use client";

import { useState, useEffect } from "react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import { Skeleton } from "@/components/ui/skeleton";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Save, AlertCircle, Clock, Mail, Webhook, RefreshCw, Power, PowerOff, Plus, Edit, Trash2 } from "lucide-react";
import { getAlertSettings, saveAlertSettings, getAlertRules, createAlertRule, updateAlertRule, deleteAlertRule, enableAlertRule, disableAlertRule, AlertSettings, AlertRule, AlertRuleCreate } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";
import { PermissionGuard } from "@/components/permissions/permission-guard";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Textarea } from "@/components/ui/textarea";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

export default function AlertsSettingsPage() {
  const { toast } = useToast();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [settings, setSettings] = useState<AlertSettings>({
    error_rate_threshold: 5.0,
    max_response_time: 2000,
    notification_method: "email",
    email_recipients: "admin@example.com",
    webhook_url: "",
    webhook_enabled: false,
  });
  const [alertRules, setAlertRules] = useState<AlertRule[]>([]);
  const [rulesLoading, setRulesLoading] = useState(true);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [editingRule, setEditingRule] = useState<AlertRule | null>(null);
  const [newRule, setNewRule] = useState<AlertRuleCreate>({
    name: "",
    rule_type: "error_rate",
    alert_level: "warning",
    threshold_value: 0,
    threshold_operator: ">",
    enabled: true,
    notification_method: "email",
    notification_target: "",
    description: "",
  });

  useEffect(() => {
    loadSettings();
    loadAlertRules();
  }, []);
  
  const loadAlertRules = async () => {
    try {
      setRulesLoading(true);
      const result = await getAlertRules();
      
      if (result.ok && result.data) {
        setAlertRules(result.data.items || []);
      } else if (result.error) {
        toast({
          title: "加載失敗",
          description: result.error.message || "無法加載告警規則",
          variant: "destructive",
        });
      }
    } catch (err) {
      console.error("Failed to load alert rules:", err);
      toast({
        title: "加載失敗",
        description: err instanceof Error ? err.message : "無法加載告警規則",
        variant: "destructive",
      });
    } finally {
      setRulesLoading(false);
    }
  };
  
  const handleToggleRule = async (ruleId: string, enabled: boolean) => {
    try {
      const result = enabled 
        ? await enableAlertRule(ruleId)
        : await disableAlertRule(ruleId);
      
      if (result.ok && result.data) {
        setAlertRules((prev) =>
          prev.map((rule) => (rule.id === ruleId ? result.data! : rule))
        );
      }
    } catch (err) {
      toast({
        title: "操作失敗",
        description: err instanceof Error ? err.message : "無法更新告警規則",
        variant: "destructive",
      });
    }
  };

  const handleCreateRule = async () => {
    try {
      if (!newRule.name || !newRule.notification_target) {
        toast({
          title: "驗證失敗",
          description: "請填寫規則名稱和通知目標",
          variant: "destructive",
        });
        return;
      }

      const result = await createAlertRule(newRule);
      
      if (result.ok && result.data) {
        setAlertRules((prev) => [...prev, result.data!]);
        setCreateDialogOpen(false);
        setNewRule({
          name: "",
          rule_type: "error_rate",
          alert_level: "warning",
          threshold_value: 0,
          threshold_operator: ">",
          enabled: true,
          notification_method: "email",
          notification_target: "",
          description: "",
        });
      }
    } catch (err) {
      toast({
        title: "創建失敗",
        description: err instanceof Error ? err.message : "無法創建告警規則",
        variant: "destructive",
      });
    }
  };

  const handleEditRule = async () => {
    if (!editingRule) return;

    try {
      const updates = {
        name: editingRule.name,
        rule_type: editingRule.rule_type,
        alert_level: editingRule.alert_level,
        threshold_value: editingRule.threshold_value,
        threshold_operator: editingRule.threshold_operator,
        enabled: editingRule.enabled,
        notification_method: editingRule.notification_method,
        notification_target: editingRule.notification_target,
        description: editingRule.description,
      };

      const result = await updateAlertRule(editingRule.id, updates);
      
      if (result.ok && result.data) {
        setAlertRules((prev) =>
          prev.map((rule) => (rule.id === editingRule.id ? result.data! : rule))
        );
        setEditDialogOpen(false);
        setEditingRule(null);
      }
    } catch (err) {
      toast({
        title: "更新失敗",
        description: err instanceof Error ? err.message : "無法更新告警規則",
        variant: "destructive",
      });
    }
  };

  const handleDeleteRule = async (ruleId: string) => {
    if (!confirm("確定要刪除此告警規則嗎？")) {
      return;
    }

    try {
      const result = await deleteAlertRule(ruleId);
      
      if (result.ok) {
        setAlertRules((prev) => prev.filter((rule) => rule.id !== ruleId));
      }
    } catch (err) {
      toast({
        title: "刪除失敗",
        description: err instanceof Error ? err.message : "無法刪除告警規則",
        variant: "destructive",
      });
    }
  };

  const openEditDialog = (rule: AlertRule) => {
    setEditingRule({ ...rule });
    setEditDialogOpen(true);
  };

  const loadSettings = async () => {
    try {
      setLoading(true);
      setError(null);
      const result = await getAlertSettings();
      
      if (result.error) {
        setError(new Error(result.error.message || "無法載入告警設置"));
        toast({
          title: "載入失敗",
          description: result.error.message || "無法載入告警設置",
          variant: "destructive",
        });
        // 如果有 mock 數據，使用 mock 數據
        if (result._isMock && result.data) {
          setSettings(result.data);
        }
      } else if (result.data) {
        setSettings(result.data);
      } else {
        setError(new Error("無法載入告警設置：未返回數據"));
      }
    } catch (err) {
      setError(err instanceof Error ? err : new Error("無法載入告警設置"));
      toast({
        title: "載入失敗",
        description: err instanceof Error ? err.message : "無法載入告警設置",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    try {
      setSaving(true);
      const result = await saveAlertSettings(settings);
      
      if (result.error) {
        toast({
          title: "保存失敗",
          description: result.error.message || "無法保存告警設置",
          variant: "destructive",
        });
      } else if (result.data) {
        toast({
          title: "保存成功",
          description: result.data.message || "告警設置已保存",
        });
      }
    } catch (err) {
      toast({
        title: "保存失敗",
        description: err instanceof Error ? err.message : "無法保存告警設置",
        variant: "destructive",
      });
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex-1 space-y-6 p-6">
        <Skeleton className="h-9 w-48" />
        <div className="grid gap-6 lg:grid-cols-2">
          <Skeleton className="h-64" />
          <Skeleton className="h-64" />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex-1 space-y-6 p-6">
        <Card className="border-destructive">
          <CardHeader>
            <CardTitle className="text-destructive">載入失敗</CardTitle>
            <CardDescription>
              {error.message || "無法連接到後端服務器，請檢查後端服務是否正在運行"}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Button onClick={loadSettings} variant="outline">
              <RefreshCw className="mr-2 h-4 w-4" />
              重試
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <PermissionGuard permission="alert_rule:view" fallback={
      <div className="flex-1 space-y-6 p-6">
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>您沒有權限查看告警設置</AlertDescription>
        </Alert>
      </div>
    }>
      <div className="flex-1 space-y-6 p-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-foreground">
            告警設置
          </h1>
          <p className="text-muted-foreground mt-2">
            配置系統監控和告警規則
          </p>
        </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* 閾值設置 */}
        <Card className="shadow-sm">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <AlertCircle className="h-5 w-5" />
              告警閾值
            </CardTitle>
            <CardDescription>
              設置觸發告警的臨界值
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="error-rate">錯誤率閾值 (%)</Label>
              <div className="flex items-center gap-2">
                <Input
                  id="error-rate"
                  type="number"
                  min="0"
                  max="100"
                  step="0.1"
                  value={settings.error_rate_threshold}
                  onChange={(e) => setSettings({ ...settings, error_rate_threshold: parseFloat(e.target.value) || 0 })}
                  className="flex-1"
                />
                <Badge variant="outline" className="text-xs">
                  當前: {settings.error_rate_threshold}%
                </Badge>
              </div>
              <p className="text-xs text-muted-foreground">
                當錯誤率超過此值時觸發告警
              </p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="response-time" className="flex items-center gap-2">
                <Clock className="h-4 w-4" />
                最大允許響應時間 (ms)
              </Label>
              <div className="flex items-center gap-2">
                <Input
                  id="response-time"
                  type="number"
                  min="100"
                  step="100"
                  value={settings.max_response_time}
                  onChange={(e) => setSettings({ ...settings, max_response_time: parseInt(e.target.value) || 0 })}
                  className="flex-1"
                />
                <Badge variant="outline" className="text-xs">
                  當前: {settings.max_response_time}ms
                </Badge>
              </div>
              <p className="text-xs text-muted-foreground">
                當平均響應時間超過此值時觸發告警
              </p>
            </div>
          </CardContent>
        </Card>

        {/* 通知方式 */}
        <Card className="shadow-sm">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Mail className="h-5 w-5" />
              通知方式
            </CardTitle>
            <CardDescription>
              配置告警通知的發送方式
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="notification-method">通知方式</Label>
              <Select
                value={settings.notification_method}
                onValueChange={(value) => setSettings({ ...settings, notification_method: value as "email" | "webhook" })}
              >
                <SelectTrigger id="notification-method">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="email">郵件通知</SelectItem>
                  <SelectItem value="webhook">Webhook</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label htmlFor="email-toggle">啟用郵件通知</Label>
                <div className="flex items-center gap-2">
                  <Switch
                    id="email-toggle"
                    checked={settings.notification_method === "email"}
                    onCheckedChange={(checked) => setSettings({ ...settings, notification_method: checked ? "email" : "webhook" })}
                  />
                </div>
              </div>
              {settings.notification_method === "email" && (
                <div className="space-y-2 pl-6">
                  <Label htmlFor="email-recipients">收件人（逗號分隔）</Label>
                  <Input
                    id="email-recipients"
                    type="text"
                    placeholder="admin@example.com, team@example.com"
                    value={settings.email_recipients || ""}
                    onChange={(e) => setSettings({ ...settings, email_recipients: e.target.value })}
                  />
                </div>
              )}
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label htmlFor="webhook-toggle" className="flex items-center gap-2">
                  <Webhook className="h-4 w-4" />
                  啟用 Webhook
                </Label>
                <Switch
                  id="webhook-toggle"
                  checked={settings.webhook_enabled}
                  onCheckedChange={(checked) => setSettings({ ...settings, webhook_enabled: checked })}
                />
              </div>
              {settings.webhook_enabled && (
                <div className="space-y-2 pl-6">
                  <Label htmlFor="webhook-url">Webhook URL</Label>
                  <Input
                    id="webhook-url"
                    type="url"
                    placeholder="https://example.com/webhook"
                    value={settings.webhook_url || ""}
                    onChange={(e) => setSettings({ ...settings, webhook_url: e.target.value })}
                  />
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

        {/* 保存按鈕 */}
        <PermissionGuard permission="alert_rule:update">
          <div className="flex justify-end">
            <Button onClick={handleSave} size="lg" disabled={saving}>
              <Save className="mr-2 h-4 w-4" />
              {saving ? "保存中..." : "保存設置"}
            </Button>
          </div>
        </PermissionGuard>

      {/* 告警規則列表 */}
      <Card className="shadow-sm mt-6">
        <CardHeader>
          <CardTitle>告警規則列表</CardTitle>
          <CardDescription>
            管理系統告警規則，可以啟用或禁用特定規則
          </CardDescription>
        </CardHeader>
        <CardContent>
          {rulesLoading ? (
            <div className="space-y-2">
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-full" />
            </div>
          ) : alertRules.length > 0 ? (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>規則名稱</TableHead>
                  <TableHead>監控指標</TableHead>
                  <TableHead>閾值</TableHead>
                  <TableHead>運算符</TableHead>
                  <TableHead>時間窗口</TableHead>
                  <TableHead>通知方式</TableHead>
                  <TableHead>狀態</TableHead>
                  <TableHead className="text-right">操作</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {alertRules.map((rule) => (
                  <TableRow key={rule.id}>
                    <TableCell className="font-medium">{rule.name}</TableCell>
                    <TableCell>
                      <Badge variant="outline">{rule.rule_type}</Badge>
                    </TableCell>
                    <TableCell>{rule.threshold_value}</TableCell>
                    <TableCell>
                      <Badge variant="secondary">{rule.threshold_operator}</Badge>
                    </TableCell>
                    <TableCell>{rule.rule_conditions?.time_window || "-"} {rule.rule_conditions?.time_window ? "秒" : ""}</TableCell>
                    <TableCell>
                      <Badge variant="outline">{rule.notification_method}</Badge>
                    </TableCell>
                    <TableCell>
                      <Badge variant={rule.enabled ? "default" : "secondary"}>
                        {rule.enabled ? "啟用" : "禁用"}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-right">
                      <PermissionGuard permission={rule.enabled ? "alert_rule:disable" : "alert_rule:enable"}>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleToggleRule(rule.id, !rule.enabled)}
                        >
                          {rule.enabled ? (
                            <>
                              <PowerOff className="h-4 w-4 mr-1" />
                              禁用
                            </>
                          ) : (
                            <>
                              <Power className="h-4 w-4 mr-1" />
                              啟用
                            </>
                          )}
                        </Button>
                      </PermissionGuard>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          ) : (
            <div className="text-center py-8 text-muted-foreground">
              暫無告警規則
            </div>
          )}
        </CardContent>
      </Card>
      </div>
    </PermissionGuard>
  );
}

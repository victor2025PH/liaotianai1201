"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  MessageSquare,
  FileText,
  Settings,
  Zap,
  Activity,
  Users,
  Server,
  UserPlus,
  BookOpen,
  UserCog,
  Monitor,
  Shield,
  Phone,
} from "lucide-react";
import { cn } from "@/lib/utils";
import {
  Sheet,
  SheetContent,
  SheetTrigger,
} from "@/components/ui/sheet";
import { Button } from "@/components/ui/button";
import { Menu } from "lucide-react";

const navigation = [
  {
    name: "總覽",
    href: "/",
    icon: LayoutDashboard,
    step: null,
    description: "系統總覽和快速訪問",
  },
  {
    name: "節點管理",
    href: "/group-ai/nodes",
    icon: Monitor,
    step: null,
    description: "管理本地電腦和遠程服務器",
  },
  {
    name: "Telegram 註冊",
    href: "/group-ai/telegram-register",
    icon: Phone,
    step: null,
    description: "註冊新的 Telegram 賬號並生成 Session 文件",
  },
  // ========== 階段一：基礎準備 ==========
  {
    name: "① 劇本管理",
    href: "/group-ai/scripts",
    icon: BookOpen,
    step: 1,
    description: "第一步：創建和管理對話劇本（必需）",
  },
  // ========== 階段二：賬號管理 ==========
  {
    name: "② 賬號管理",
    href: "/group-ai/accounts",
    icon: UserPlus,
    step: 2,
    description: "第二步：創建和管理 Telegram 賬號（需關聯劇本）",
  },
  // ========== 階段三：角色分配（可選）==========
  {
    name: "③ 角色分配",
    href: "/group-ai/role-assignments",
    icon: UserCog,
    step: 3,
    description: "第三步（可選）：從劇本提取角色並分配給賬號",
  },
  {
    name: "④ 分配方案",
    href: "/group-ai/role-assignment-schemes",
    icon: Settings,
    step: 4,
    description: "第四步（可選）：保存和重用角色分配方案",
  },
  // ========== 階段五：自動化任務（可選）==========
  {
    name: "⑤ 自動化任務",
    href: "/group-ai/automation-tasks",
    icon: Zap,
    step: 5,
    description: "第五步（可選）：配置自動化執行任務",
  },
  // ========== 監控和管理 ==========
  {
    name: "群組監控",
    href: "/group-ai/groups",
    icon: Monitor,
    step: null,
    description: "監控群組活動和消息",
  },
  {
    name: "會話列表",
    href: "/sessions",
    icon: MessageSquare,
    step: null,
    description: "查看和管理會話記錄",
  },
  {
    name: "日誌",
    href: "/logs",
    icon: FileText,
    step: null,
    description: "查看系統日誌",
  },
  {
    name: "系統監控",
    href: "/monitoring",
    icon: Activity,
    step: null,
    description: "系統性能監控",
  },
  {
    name: "告警設置",
    href: "/settings/alerts",
    icon: Settings,
    step: null,
    description: "配置告警規則",
  },
  {
    name: "權限管理",
    href: "/permissions",
    icon: Shield,
    step: null,
    description: "用戶和權限管理",
  },
];

function SidebarContent() {
  const pathname = usePathname();

  return (
    <>
      <div className="flex h-16 items-center border-b border-border px-6">
        <h1 className="text-lg font-semibold text-foreground">聊天 AI 控制台</h1>
      </div>
      <nav className="flex-1 space-y-1 px-3 py-4">
        {navigation.map((item, index) => {
          const isActive = pathname === item.href || pathname?.startsWith(item.href + "/");
          const isStep = item.step !== null;
          const showDivider = index > 0 && 
            ((item.step === 2 && navigation[index - 1].step === 1) ||
             (item.step === 3 && navigation[index - 1].step === 2) ||
             (item.step === 4 && navigation[index - 1].step === 3) ||
             (item.step === 5 && navigation[index - 1].step === 4));
          
          return (
            <div key={item.name}>
              {showDivider && (
                <div className="my-2 mx-3 border-t border-border/50" />
              )}
              <Link
                href={item.href}
                className={cn(
                  "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors group relative",
                  isActive
                    ? "bg-primary text-primary-foreground"
                    : "text-muted-foreground hover:bg-muted hover:text-foreground",
                  isStep && "font-semibold"
                )}
                title={item.description}
              >
                <item.icon className="h-4 w-4 flex-shrink-0" />
                <span className="flex-1">{item.name}</span>
                {isStep && (
                  <span className={cn(
                    "text-xs px-1.5 py-0.5 rounded",
                    isActive 
                      ? "bg-primary-foreground/20 text-primary-foreground"
                      : "bg-muted text-muted-foreground opacity-60"
                  )}>
                    步驟{item.step}
                  </span>
                )}
              </Link>
            </div>
          );
        })}
      </nav>
      <div className="border-t border-border p-4">
        <div className="rounded-lg bg-muted/50 p-3">
          <p className="text-xs font-medium text-foreground">環境</p>
          <p className="text-xs text-muted-foreground">Production</p>
        </div>
      </div>
    </>
  );
}

export function Sidebar() {
  return (
    <>
      {/* 桌面端側邊欄 */}
      <div className="hidden lg:flex h-screen w-64 flex-col border-r border-border bg-card">
        <SidebarContent />
      </div>

      {/* 移動端抽屜 */}
      <Sheet>
        <SheetTrigger asChild>
          <Button
            variant="ghost"
            size="icon"
            className="lg:hidden fixed top-4 left-4 z-50"
          >
            <Menu className="h-5 w-5" />
            <span className="sr-only">打開菜單</span>
          </Button>
        </SheetTrigger>
        <SheetContent side="left" className="w-64 p-0">
          <div className="flex h-full flex-col">
            <SidebarContent />
          </div>
        </SheetContent>
      </Sheet>
    </>
  );
}


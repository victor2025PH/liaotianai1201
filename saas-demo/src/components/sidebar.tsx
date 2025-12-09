"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { memo, useMemo } from "react";
import {
  LayoutDashboard,
  MessageSquare,
  FileText,
  Settings,
  Zap,
  Activity,
  UserPlus,
  BookOpen,
  UserCog,
  Monitor,
  Shield,
  Phone,
  Menu,
  Download,
  Gift,
  Sparkles,
  Heart,
  TrendingUp,
} from "lucide-react";
import { cn } from "@/lib/utils";
import {
  Sheet,
  SheetContent,
  SheetTrigger,
} from "@/components/ui/sheet";
import { Button } from "@/components/ui/button";
import { useI18n } from "@/lib/i18n";

// 導航配置類型
interface NavItem {
  nameKey: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
  step: number | null;
  descKey: string;
}

// 導航配置
const navigationConfig: NavItem[] = [
  {
    nameKey: "dashboard",
    href: "/",
    icon: LayoutDashboard,
    step: null,
    descKey: "dashboard",
  },
  {
    nameKey: "nodeManagement",
    href: "/group-ai/nodes",
    icon: Monitor,
    step: null,
    descKey: "nodeManagement",
  },
  {
    nameKey: "chatFeatures",
    href: "/group-ai/chat-features",
    icon: Sparkles,
    step: null,
    descKey: "chatFeatures",
  },
  {
    nameKey: "advancedFeatures",
    href: "/group-ai/advanced-features",
    icon: Zap,
    step: null,
    descKey: "advancedFeatures",
  },
  {
    nameKey: "privateFunnel",
    href: "/group-ai/private-funnel",
    icon: UserPlus,
    step: null,
    descKey: "privateFunnel",
  },
  {
    nameKey: "workerDeploy",
    href: "/group-ai/worker-deploy",
    icon: Download,
    step: null,
    descKey: "workerDeploy",
  },
  {
    nameKey: "redpacketGame",
    href: "/group-ai/redpacket",
    icon: Gift,
    step: null,
    descKey: "redpacketGame",
  },
  {
    nameKey: "telegramRegister",
    href: "/group-ai/telegram-register",
    icon: Phone,
    step: null,
    descKey: "telegramRegister",
  },
  {
    nameKey: "scriptManagement",
    href: "/group-ai/scripts",
    icon: BookOpen,
    step: 1,
    descKey: "scriptManagement",
  },
  {
    nameKey: "accountManagement",
    href: "/group-ai/accounts",
    icon: UserPlus,
    step: 2,
    descKey: "accountManagement",
  },
  {
    nameKey: "roleAssignment",
    href: "/group-ai/role-assignments",
    icon: UserCog,
    step: 3,
    descKey: "roleAssignment",
  },
  {
    nameKey: "allocationScheme",
    href: "/group-ai/role-assignment-schemes",
    icon: Settings,
    step: 4,
    descKey: "allocationScheme",
  },
  {
    nameKey: "automationTasks",
    href: "/group-ai/automation-tasks",
    icon: Zap,
    step: 5,
    descKey: "automationTasks",
  },
  {
    nameKey: "groupMonitor",
    href: "/group-ai/groups",
    icon: Monitor,
    step: null,
    descKey: "groupMonitor",
  },
  {
    nameKey: "sessionList",
    href: "/sessions",
    icon: MessageSquare,
    step: null,
    descKey: "sessionList",
  },
  {
    nameKey: "logs",
    href: "/logs",
    icon: FileText,
    step: null,
    descKey: "logs",
  },
  {
    nameKey: "systemMonitor",
    href: "/monitoring",
    icon: Activity,
    step: null,
    descKey: "systemMonitor",
  },
  {
    nameKey: "healthCheck",
    href: "/health",
    icon: Heart,
    step: null,
    descKey: "healthCheck",
  },
  {
    nameKey: "performanceMonitor",
    href: "/performance",
    icon: TrendingUp,
    step: null,
    descKey: "performanceMonitor",
  },
  {
    nameKey: "alertSettings",
    href: "/settings/alerts",
    icon: Settings,
    step: null,
    descKey: "alertSettings",
  },
  {
    nameKey: "permissionManagement",
    href: "/permissions",
    icon: Shield,
    step: null,
    descKey: "permissionManagement",
  },
];

// 步骤数字映射
const stepNumbers: Record<number, string> = {
  1: "①",
  2: "②",
  3: "③",
  4: "④",
  5: "⑤",
};

// 單個導航項組件（memo 優化）
const NavItemComponent = memo(({ 
  item, 
  isActive, 
  showDivider,
  name,
  stepText,
  optionalText,
}: { 
  item: NavItem;
  isActive: boolean;
  showDivider: boolean;
  name: string;
  stepText: string;
  optionalText: string;
}) => {
  const isStep = item.step !== null;
  const Icon = item.icon;
  const displayName = isStep ? `${stepNumbers[item.step!]} ${name}` : name;
  
  return (
    <div>
      {showDivider && <div className="my-2 mx-3 border-t border-border/50" />}
      <Link
        href={item.href}
        prefetch={true}
        className={cn(
          "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors group relative",
          isActive
            ? "bg-primary text-primary-foreground"
            : "text-muted-foreground hover:bg-muted hover:text-foreground",
          isStep && "font-semibold"
        )}
      >
        <Icon className="h-4 w-4 flex-shrink-0" />
        <span className="flex-1">{displayName}</span>
        {isStep && (
          <span className={cn(
            "text-xs px-1.5 py-0.5 rounded",
            isActive 
              ? "bg-primary-foreground/20 text-primary-foreground"
              : "bg-muted text-muted-foreground opacity-60"
          )}>
            {stepText}{item.step}
          </span>
        )}
      </Link>
    </div>
  );
});
NavItemComponent.displayName = 'NavItemComponent';

// SidebarContent 使用 memo 優化
const SidebarContent = memo(function SidebarContent() {
  const pathname = usePathname();
  const { t, language } = useI18n();

  // 使用 useMemo 緩存導航項的渲染結果
  const navItems = useMemo(() => {
    return navigationConfig.map((item, index) => {
      const isActive = pathname === item.href || pathname?.startsWith(item.href + "/");
      const showDivider = index > 0 && 
        ((item.step === 2 && navigationConfig[index - 1].step === 1) ||
         (item.step === 3 && navigationConfig[index - 1].step === 2) ||
         (item.step === 4 && navigationConfig[index - 1].step === 3) ||
         (item.step === 5 && navigationConfig[index - 1].step === 4));
      
      const name = t.nav[item.nameKey as keyof typeof t.nav] || item.nameKey;
      
      return (
        <NavItemComponent 
          key={item.href}
          item={item}
          isActive={isActive}
          showDivider={showDivider}
          name={name}
          stepText={t.nav.step}
          optionalText={t.nav.optional}
        />
      );
    });
  }, [pathname, t, language]);

  return (
    <>
      <div className="flex h-16 items-center border-b border-border px-6">
        <h1 className="text-lg font-semibold text-foreground">{t.header.title}</h1>
      </div>
      <nav className="flex-1 space-y-1 px-3 py-4">
        {navItems}
      </nav>
      <div className="border-t border-border p-4">
        <div className="rounded-lg bg-muted/50 p-3">
          <p className="text-xs font-medium text-foreground">
            {t.header.environment}
          </p>
          <p className="text-xs text-muted-foreground">{t.header.production}</p>
        </div>
      </div>
    </>
  );
});

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
            <span className="sr-only">打开菜单</span>
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

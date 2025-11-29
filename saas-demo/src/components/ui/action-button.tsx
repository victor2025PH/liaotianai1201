"use client";

import { Button, ButtonProps } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import {
  Plus,
  RefreshCw,
  Edit,
  Trash2,
  Play,
  Download,
  Upload,
  Search,
  Eye,
  EyeOff,
  Send,
  Check,
  X,
  Save,
  Copy,
  Settings,
  Filter,
  RotateCcw,
  History,
  Scan,
  Folder,
} from "lucide-react";
import { forwardRef } from "react";

export type ActionType =
  | "create"
  | "refresh"
  | "edit"
  | "delete"
  | "play"
  | "download"
  | "upload"
  | "search"
  | "view"
  | "hide"
  | "submit"
  | "approve"
  | "reject"
  | "save"
  | "copy"
  | "settings"
  | "filter"
  | "revert"
  | "history"
  | "scan"
  | "scanFolder";

interface ActionButtonProps extends Omit<ButtonProps, "variant"> {
  actionType: ActionType;
  label?: string;
  showIcon?: boolean;
  showLabel?: boolean;
  prominent?: boolean; // 是否突出显示（主要操作按钮）
}

const actionConfig: Record<
  ActionType,
  {
    icon: React.ElementType;
    defaultLabel: string;
    prominentClass: string;
    normalClass: string;
  }
> = {
  create: {
    icon: Plus,
    defaultLabel: "创建",
    prominentClass:
      "bg-gradient-to-r from-emerald-500 to-green-600 hover:from-emerald-600 hover:to-green-700 text-white border-0 shadow-lg shadow-emerald-500/25",
    normalClass: "bg-primary text-primary-foreground hover:bg-primary/90",
  },
  refresh: {
    icon: RefreshCw,
    defaultLabel: "刷新",
    prominentClass: "bg-blue-500 hover:bg-blue-600 text-white border-0",
    normalClass: "border-border hover:bg-accent",
  },
  edit: {
    icon: Edit,
    defaultLabel: "编辑",
    prominentClass: "bg-amber-500 hover:bg-amber-600 text-white border-0",
    normalClass: "border-border hover:bg-accent",
  },
  delete: {
    icon: Trash2,
    defaultLabel: "删除",
    prominentClass:
      "bg-gradient-to-r from-red-500 to-rose-600 hover:from-red-600 hover:to-rose-700 text-white border-0 shadow-lg shadow-red-500/25",
    normalClass: "bg-destructive text-destructive-foreground hover:bg-destructive/90",
  },
  play: {
    icon: Play,
    defaultLabel: "运行",
    prominentClass:
      "bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700 text-white border-0",
    normalClass: "bg-green-600 hover:bg-green-700 text-white",
  },
  download: {
    icon: Download,
    defaultLabel: "下载",
    prominentClass: "bg-blue-500 hover:bg-blue-600 text-white border-0",
    normalClass: "border-border hover:bg-accent",
  },
  upload: {
    icon: Upload,
    defaultLabel: "上传",
    prominentClass: "bg-purple-500 hover:bg-purple-600 text-white border-0",
    normalClass: "border-border hover:bg-accent",
  },
  search: {
    icon: Search,
    defaultLabel: "搜索",
    prominentClass: "bg-blue-500 hover:bg-blue-600 text-white border-0",
    normalClass: "border-border hover:bg-accent",
  },
  view: {
    icon: Eye,
    defaultLabel: "查看",
    prominentClass: "bg-blue-500 hover:bg-blue-600 text-white border-0",
    normalClass: "border-border hover:bg-accent",
  },
  hide: {
    icon: EyeOff,
    defaultLabel: "隐藏",
    prominentClass: "bg-gray-500 hover:bg-gray-600 text-white border-0",
    normalClass: "border-border hover:bg-accent",
  },
  submit: {
    icon: Send,
    defaultLabel: "提交",
    prominentClass:
      "bg-gradient-to-r from-blue-500 to-indigo-600 hover:from-blue-600 hover:to-indigo-700 text-white border-0 shadow-lg shadow-blue-500/25",
    normalClass: "bg-blue-600 hover:bg-blue-700 text-white",
  },
  approve: {
    icon: Check,
    defaultLabel: "通过",
    prominentClass: "bg-green-500 hover:bg-green-600 text-white border-0",
    normalClass: "bg-green-600 hover:bg-green-700 text-white",
  },
  reject: {
    icon: X,
    defaultLabel: "拒绝",
    prominentClass: "bg-red-500 hover:bg-red-600 text-white border-0",
    normalClass: "bg-red-600 hover:bg-red-700 text-white",
  },
  save: {
    icon: Save,
    defaultLabel: "保存",
    prominentClass:
      "bg-gradient-to-r from-blue-500 to-cyan-600 hover:from-blue-600 hover:to-cyan-700 text-white border-0",
    normalClass: "bg-blue-600 hover:bg-blue-700 text-white",
  },
  copy: {
    icon: Copy,
    defaultLabel: "复制",
    prominentClass: "bg-gray-500 hover:bg-gray-600 text-white border-0",
    normalClass: "border-border hover:bg-accent",
  },
  settings: {
    icon: Settings,
    defaultLabel: "设置",
    prominentClass: "bg-gray-600 hover:bg-gray-700 text-white border-0",
    normalClass: "border-border hover:bg-accent",
  },
  filter: {
    icon: Filter,
    defaultLabel: "筛选",
    prominentClass: "bg-indigo-500 hover:bg-indigo-600 text-white border-0",
    normalClass: "border-border hover:bg-accent",
  },
  revert: {
    icon: RotateCcw,
    defaultLabel: "还原",
    prominentClass: "bg-amber-500 hover:bg-amber-600 text-white border-0",
    normalClass: "border-border hover:bg-accent",
  },
  history: {
    icon: History,
    defaultLabel: "历史",
    prominentClass: "bg-purple-500 hover:bg-purple-600 text-white border-0",
    normalClass: "border-border hover:bg-accent",
  },
  scan: {
    icon: Scan,
    defaultLabel: "扫描",
    prominentClass:
      "bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-600 hover:to-blue-700 text-white border-0 shadow-lg shadow-cyan-500/25",
    normalClass: "bg-cyan-600 hover:bg-cyan-700 text-white",
  },
  scanFolder: {
    icon: Folder,
    defaultLabel: "扫描文件夹",
    prominentClass:
      "bg-gradient-to-r from-violet-500 to-purple-600 hover:from-violet-600 hover:to-purple-700 text-white border-0 shadow-lg shadow-violet-500/25",
    normalClass: "bg-violet-600 hover:bg-violet-700 text-white",
  },
};

export const ActionButton = forwardRef<HTMLButtonElement, ActionButtonProps>(
  (
    {
      actionType,
      label,
      showIcon = true,
      showLabel = true,
      prominent = false,
      className,
      size = "default",
      disabled,
      children,
      ...props
    },
    ref
  ) => {
    const config = actionConfig[actionType];
    const Icon = config.icon;
    const displayLabel = label || config.defaultLabel;

    // 确定按钮大小class
    const sizeClass = size === "sm" ? "h-8 px-3 text-xs" : size === "lg" ? "h-11 px-8" : "h-9 px-4";

    // 主要创建按钮始终使用突出样式
    const isPrimaryAction = actionType === "create" || actionType === "scan" || actionType === "scanFolder";
    const useProminent = prominent || isPrimaryAction;

    const buttonClass = cn(
      "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md font-medium transition-all duration-200",
      "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
      "disabled:pointer-events-none disabled:opacity-50",
      sizeClass,
      useProminent ? config.prominentClass : `border ${config.normalClass}`,
      className
    );

    return (
      <Button ref={ref} className={buttonClass} disabled={disabled} {...props}>
        {showIcon && <Icon className={cn("flex-shrink-0", size === "sm" ? "h-3.5 w-3.5" : "h-4 w-4")} />}
        {showLabel && <span>{children || displayLabel}</span>}
      </Button>
    );
  }
);

ActionButton.displayName = "ActionButton";

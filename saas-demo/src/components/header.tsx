"use client";

import { useRouter } from "next/navigation";
import { ThemeToggle } from "@/components/theme-toggle";
import { NotificationCenter } from "@/components/notification-center";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { logout, getToken } from "@/lib/api/auth";
import { LogIn, LogOut } from "lucide-react";
import { useEffect, useState } from "react";

export function Header() {
  const router = useRouter();
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  useEffect(() => {
    setIsAuthenticated(getToken() !== null);
  }, []);

  const handleLogin = () => {
    router.push("/login");
  };

  const handleLogout = () => {
    logout();
    setIsAuthenticated(false);
  };

  return (
    <header className="sticky top-0 z-40 flex h-16 items-center justify-between border-b border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 px-6">
      <div className="flex items-center gap-4">
        <h2 className="text-lg font-semibold text-foreground lg:hidden">
          聊天 AI 控制台
        </h2>
      </div>
      <div className="flex items-center gap-3">
        <Badge variant="outline" className="px-3 py-1">
          Production
        </Badge>
        <NotificationCenter />
        <ThemeToggle />
        {isAuthenticated ? (
          <Button
            variant="ghost"
            size="sm"
            onClick={handleLogout}
            className="gap-2"
          >
            <LogOut className="h-4 w-4" />
            登出
          </Button>
        ) : (
          <Button
            variant="outline"
            size="sm"
            onClick={handleLogin}
            className="gap-2"
          >
            <LogIn className="h-4 w-4" />
            登錄
          </Button>
        )}
      </div>
    </header>
  );
}


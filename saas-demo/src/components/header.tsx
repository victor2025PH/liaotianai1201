"use client";

import { useRouter } from "next/navigation";
import { ThemeToggle } from "@/components/theme-toggle";
import { NotificationCenter } from "@/components/notification-center";
import { LanguageToggle } from "@/components/language-toggle";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { logout, getToken } from "@/lib/api/auth";
import { LogIn, LogOut, BookOpen, GraduationCap } from "lucide-react";
import { useEffect, useState, useCallback } from "react";
import { useI18n } from "@/lib/i18n";
import { OnboardingTour, resetOnboarding } from "@/components/onboarding/onboarding-tour";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";

export function Header() {
  const router = useRouter();
  const { t } = useI18n();
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [showTour, setShowTour] = useState(false);

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

  const handleLearn = useCallback(() => {
    resetOnboarding();
    setShowTour(true);
  }, []);

  const handleTourClose = useCallback(() => {
    setShowTour(false);
  }, []);

  return (
    <>
      <header className="sticky top-0 z-40 flex h-16 items-center justify-between border-b border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 px-6">
        <div className="flex items-center gap-4">
          <h2 className="text-lg font-semibold text-foreground lg:hidden">
            {t.header.title}
          </h2>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="outline" className="px-3 py-1 hidden sm:inline-flex">
            {t.header.production}
          </Badge>
          
          {/* 学习按钮 */}
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={handleLearn}
                  className="h-9 w-9 text-primary hover:text-primary hover:bg-primary/10"
                >
                  <GraduationCap className="h-5 w-5" />
                  <span className="sr-only">{t.common.learn}</span>
                </Button>
              </TooltipTrigger>
              <TooltipContent>
                <p>{t.header.learnMore}</p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>

          <NotificationCenter />
          <LanguageToggle />
          <ThemeToggle />
          
          {isAuthenticated ? (
            <Button
              variant="ghost"
              size="sm"
              onClick={handleLogout}
              className="gap-2"
            >
              <LogOut className="h-4 w-4" />
              <span className="hidden sm:inline">{t.header.logout}</span>
            </Button>
          ) : (
            <Button
              variant="outline"
              size="sm"
              onClick={handleLogin}
              className="gap-2"
            >
              <LogIn className="h-4 w-4" />
              <span className="hidden sm:inline">{t.header.login}</span>
            </Button>
          )}
        </div>
      </header>

      {/* 引导教程 */}
      {showTour && <OnboardingTour forceShow onClose={handleTourClose} />}
    </>
  );
}

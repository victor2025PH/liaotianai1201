"use client";

import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState, useCallback, useMemo, memo } from "react";
import dynamic from "next/dynamic";
import { isAuthenticated } from "@/lib/api/auth";
import { I18nProvider, useI18n } from "@/lib/i18n";
import { OnboardingTour, isOnboardingCompleted } from "@/components/onboarding/onboarding-tour";

// 懶加載 Sidebar 和 Header（非首屏關鍵組件）
const Sidebar = dynamic(() => import("@/components/sidebar").then(m => ({ default: m.Sidebar })), {
  ssr: false,
  loading: () => <div className="hidden lg:block w-64 bg-card border-r border-border" />
});

const Header = dynamic(() => import("@/components/header").then(m => ({ default: m.Header })), {
  ssr: false,
  loading: () => <div className="h-14 border-b border-border bg-card" />
});

// 載入動畫組件（輕量級）
const LoadingSpinner = memo(() => {
  // 使用 try-catch 處理可能的 context 未初始化情況
  let loadingText = "加载中...";
  try {
    const { t } = useI18n();
    loadingText = t.common.loading;
  } catch {
    // 使用默認文本
  }
  
  return (
    <div className="flex h-screen items-center justify-center">
      <div className="text-center">
        <div className="mb-4 h-8 w-8 animate-spin rounded-full border-4 border-gray-300 border-t-blue-600 mx-auto"></div>
        <p className="text-sm text-gray-500">{loadingText}</p>
      </div>
    </div>
  );
});
LoadingSpinner.displayName = 'LoadingSpinner';

// 主佈局組件
const MainLayout = memo(({ children }: { children: React.ReactNode }) => {
  const [showOnboarding, setShowOnboarding] = useState(false);

  useEffect(() => {
    // 检查是否需要显示引导
    if (!isOnboardingCompleted()) {
      setShowOnboarding(true);
    }
  }, []);

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar />
      <div className="flex flex-1 flex-col overflow-hidden">
        <Header />
        <main className="flex-1 overflow-y-auto bg-background">
          {children}
        </main>
      </div>
      {/* 首次登录引导 */}
      {showOnboarding && <OnboardingTour onClose={() => setShowOnboarding(false)} />}
    </div>
  );
});
MainLayout.displayName = 'MainLayout';

// 內部佈局組件（需要使用 I18n context）
function LayoutWrapperInner({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const isLoginPage = useMemo(() => pathname === "/login", [pathname]);
  const [checking, setChecking] = useState(!isLoginPage);
  const [isAuthed, setIsAuthed] = useState(false);

  // 優化：使用 useCallback 避免重複創建函數
  const checkAuth = useCallback(() => {
    const authenticated = isAuthenticated();
    setIsAuthed(authenticated);
    setChecking(false);
    return authenticated;
  }, []);

  useEffect(() => {
    // 登入頁不需要檢查
    if (isLoginPage) {
      const authenticated = isAuthenticated();
      if (authenticated) {
        router.replace("/");
      }
      setChecking(false);
      return;
    }

    // 立即檢查認證
    const authenticated = checkAuth();
    
    if (!authenticated) {
      window.location.href = "/login";
      return;
    }
    
    // 監聽 localStorage 變化
    const handleStorageChange = (e: StorageEvent) => {
      if (e.key === "access_token") {
        checkAuth();
      }
    };
    
    const handleTokenCleared = () => checkAuth();
    
    window.addEventListener("storage", handleStorageChange);
    window.addEventListener("tokenCleared", handleTokenCleared);
    
    // 優化：減少檢查頻率到 10 秒（減少 CPU 負載）
    const interval = setInterval(checkAuth, 10000);
    
    return () => {
      clearInterval(interval);
      window.removeEventListener("storage", handleStorageChange);
      window.removeEventListener("tokenCleared", handleTokenCleared);
    };
  }, [isLoginPage, router, checkAuth]);

  // 登入頁直接渲染
  if (isLoginPage) {
    return <>{children}</>;
  }

  // 檢查中顯示載入
  if (checking) {
    return <LoadingSpinner />;
  }

  // 未認證返回空
  if (!isAuthed) {
    return null;
  }

  return <MainLayout>{children}</MainLayout>;
}

// 導出的主組件（包含 I18n Provider）
export function LayoutWrapper({ children }: { children: React.ReactNode }) {
  return (
    <I18nProvider>
      <LayoutWrapperInner>{children}</LayoutWrapperInner>
    </I18nProvider>
  );
}


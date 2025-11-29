"use client";

import React, { useState, useEffect, useCallback } from "react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { useI18n } from "@/lib/i18n";
import {
  LayoutDashboard,
  Monitor,
  FileText,
  Users,
  UserCog,
  Settings,
  Zap,
  BookOpen,
  ChevronLeft,
  ChevronRight,
  Sparkles,
  CheckCircle2,
  Play,
  X,
} from "lucide-react";
import { cn } from "@/lib/utils";

interface OnboardingStep {
  id: string;
  icon: React.ReactNode;
  titleKey: keyof typeof import("@/lib/i18n/translations").translations["zh-CN"]["onboarding"];
  descKey: keyof typeof import("@/lib/i18n/translations").translations["zh-CN"]["onboarding"];
  highlight?: string; // CSS selector to highlight
}

const ONBOARDING_STEPS: OnboardingStep[] = [
  {
    id: "welcome",
    icon: <Sparkles className="h-12 w-12 text-primary" />,
    titleKey: "welcome",
    descKey: "welcomeDesc",
  },
  {
    id: "nav",
    icon: <LayoutDashboard className="h-12 w-12 text-blue-500" />,
    titleKey: "step1Title",
    descKey: "step1Desc",
  },
  {
    id: "nodes",
    icon: <Monitor className="h-12 w-12 text-green-500" />,
    titleKey: "step2Title",
    descKey: "step2Desc",
  },
  {
    id: "scripts",
    icon: <FileText className="h-12 w-12 text-purple-500" />,
    titleKey: "step3Title",
    descKey: "step3Desc",
  },
  {
    id: "accounts",
    icon: <Users className="h-12 w-12 text-orange-500" />,
    titleKey: "step4Title",
    descKey: "step4Desc",
  },
  {
    id: "roles",
    icon: <UserCog className="h-12 w-12 text-pink-500" />,
    titleKey: "step5Title",
    descKey: "step5Desc",
  },
  {
    id: "automation",
    icon: <Zap className="h-12 w-12 text-yellow-500" />,
    titleKey: "step6Title",
    descKey: "step6Desc",
  },
  {
    id: "monitoring",
    icon: <Settings className="h-12 w-12 text-cyan-500" />,
    titleKey: "step7Title",
    descKey: "step7Desc",
  },
  {
    id: "learn",
    icon: <BookOpen className="h-12 w-12 text-indigo-500" />,
    titleKey: "step8Title",
    descKey: "step8Desc",
  },
  {
    id: "finish",
    icon: <CheckCircle2 className="h-12 w-12 text-emerald-500" />,
    titleKey: "finishTitle",
    descKey: "finishDesc",
  },
];

const STORAGE_KEY = "onboarding-completed";

interface OnboardingTourProps {
  forceShow?: boolean;
  onClose?: () => void;
}

export function OnboardingTour({ forceShow = false, onClose }: OnboardingTourProps) {
  const { t } = useI18n();
  const [isOpen, setIsOpen] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    // 检查是否第一次访问
    if (forceShow) {
      setIsOpen(true);
      setCurrentStep(0);
    } else {
      const completed = localStorage.getItem(STORAGE_KEY);
      if (!completed) {
        setIsOpen(true);
      }
    }
  }, [forceShow]);

  const handleClose = useCallback(() => {
    setIsOpen(false);
    localStorage.setItem(STORAGE_KEY, "true");
    onClose?.();
  }, [onClose]);

  const handleSkip = useCallback(() => {
    handleClose();
  }, [handleClose]);

  const handleNext = useCallback(() => {
    if (currentStep < ONBOARDING_STEPS.length - 1) {
      setCurrentStep((prev) => prev + 1);
    } else {
      handleClose();
    }
  }, [currentStep, handleClose]);

  const handlePrev = useCallback(() => {
    if (currentStep > 0) {
      setCurrentStep((prev) => prev - 1);
    }
  }, [currentStep]);

  const handleStart = useCallback(() => {
    setCurrentStep(1);
  }, []);

  if (!mounted) return null;

  const step = ONBOARDING_STEPS[currentStep];
  const isWelcome = currentStep === 0;
  const isFinish = currentStep === ONBOARDING_STEPS.length - 1;

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DialogContent className="sm:max-w-[500px] p-0 overflow-hidden">
        {/* 进度条 */}
        <div className="h-1 bg-muted">
          <div
            className="h-full bg-primary transition-all duration-300"
            style={{ width: `${((currentStep + 1) / ONBOARDING_STEPS.length) * 100}%` }}
          />
        </div>

        <div className="p-6">
          {/* 关闭按钮 */}
          <button
            onClick={handleSkip}
            className="absolute right-4 top-4 rounded-sm opacity-70 ring-offset-background transition-opacity hover:opacity-100 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
          >
            <X className="h-4 w-4" />
            <span className="sr-only">Close</span>
          </button>

          <DialogHeader className="text-center pb-4">
            {/* 图标 */}
            <div className="flex justify-center mb-4">
              <div className="p-4 rounded-full bg-muted/50">{step.icon}</div>
            </div>

            <DialogTitle className="text-xl">
              {t.onboarding[step.titleKey as keyof typeof t.onboarding]}
            </DialogTitle>
            <DialogDescription className="text-base mt-2">
              {t.onboarding[step.descKey as keyof typeof t.onboarding]}
            </DialogDescription>
          </DialogHeader>

          {/* 步骤指示器 */}
          <div className="flex justify-center gap-1.5 my-6">
            {ONBOARDING_STEPS.map((_, index) => (
              <button
                key={index}
                onClick={() => setCurrentStep(index)}
                className={cn(
                  "w-2 h-2 rounded-full transition-all",
                  index === currentStep
                    ? "bg-primary w-6"
                    : index < currentStep
                    ? "bg-primary/50"
                    : "bg-muted-foreground/30"
                )}
              />
            ))}
          </div>

          <DialogFooter className="flex-col sm:flex-row gap-2">
            {isWelcome ? (
              <>
                <Button variant="outline" onClick={handleSkip} className="w-full sm:w-auto">
                  {t.onboarding.skipTour}
                </Button>
                <Button onClick={handleStart} className="w-full sm:w-auto gap-2">
                  <Play className="h-4 w-4" />
                  {t.onboarding.startTour}
                </Button>
              </>
            ) : isFinish ? (
              <Button onClick={handleClose} className="w-full gap-2">
                <CheckCircle2 className="h-4 w-4" />
                {t.onboarding.gotIt}
              </Button>
            ) : (
              <>
                <Button variant="outline" onClick={handlePrev} className="w-full sm:w-auto gap-2">
                  <ChevronLeft className="h-4 w-4" />
                  {t.onboarding.prev}
                </Button>
                <Button onClick={handleNext} className="w-full sm:w-auto gap-2">
                  {t.onboarding.next}
                  <ChevronRight className="h-4 w-4" />
                </Button>
              </>
            )}
          </DialogFooter>
        </div>
      </DialogContent>
    </Dialog>
  );
}

// 重置引导状态（用于测试或重新显示）
export function resetOnboarding() {
  localStorage.removeItem(STORAGE_KEY);
}

// 检查是否已完成引导
export function isOnboardingCompleted() {
  if (typeof window === "undefined") return true;
  return localStorage.getItem(STORAGE_KEY) === "true";
}


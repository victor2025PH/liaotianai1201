"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { CheckCircle2, Circle, AlertCircle, Info } from "lucide-react";
import { cn } from "@/lib/utils";
import { Alert, AlertDescription } from "@/components/ui/alert";

export interface Step {
  number: number;
  title: string;
  description: string;
  href: string;
  status: "completed" | "current" | "pending" | "optional";
}

interface StepIndicatorProps {
  currentStep: number;
  steps: Step[];
  title?: string;
  description?: string;
  guideContent?: React.ReactNode;
}

export function StepIndicator({ 
  currentStep, 
  steps, 
  title,
  description,
  guideContent 
}: StepIndicatorProps) {
  const getStepIcon = (step: Step) => {
    if (step.status === "completed") {
      return <CheckCircle2 className="h-5 w-5 text-green-600" />;
    } else if (step.status === "current") {
      return <Circle className="h-5 w-5 text-primary fill-primary" />;
    } else {
      return <Circle className="h-5 w-5 text-muted-foreground" />;
    }
  };

  const getStepBadge = (step: Step) => {
    if (step.status === "optional") {
      return <Badge variant="outline" className="ml-2">可選</Badge>;
    }
    return null;
  };

  return (
    <div className="space-y-4 mb-6">
      {title && (
        <div className="flex items-center gap-3">
          <div className="flex items-center justify-center w-10 h-10 rounded-full bg-primary text-primary-foreground font-bold text-lg">
            {currentStep}
          </div>
          <div>
            <h2 className="text-2xl font-bold">{title}</h2>
            {description && (
              <p className="text-muted-foreground text-sm mt-1">{description}</p>
            )}
          </div>
        </div>
      )}

      <Card>
        <CardHeader>
          <CardTitle className="text-base">工作流程步驟</CardTitle>
          <CardDescription>按照順序完成以下步驟以配置系統</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {steps.map((step, index) => (
              <div
                key={step.number}
                className={cn(
                  "flex items-start gap-4 p-3 rounded-lg border transition-colors",
                  step.status === "current" && "bg-primary/5 border-primary",
                  step.status === "completed" && "bg-green-50 border-green-200",
                  step.status === "pending" && "bg-muted/30 border-border"
                )}
              >
                <div className="flex-shrink-0 mt-0.5">
                  {getStepIcon(step)}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-sm">
                      步驟 {step.number}: {step.title}
                    </span>
                    {getStepBadge(step)}
                  </div>
                  <p className="text-xs text-muted-foreground mt-1">
                    {step.description}
                  </p>
                </div>
                {step.status === "current" && (
                  <Badge variant="default" className="ml-auto">
                    當前步驟
                  </Badge>
                )}
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {guideContent && (
        <Alert>
          <Info className="h-4 w-4" />
          <AlertDescription>
            <div className="space-y-2">
              {guideContent}
            </div>
          </AlertDescription>
        </Alert>
      )}
    </div>
  );
}


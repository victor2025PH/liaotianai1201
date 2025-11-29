"use client";

import { Badge } from "@/components/ui/badge";
import { CheckCircle2, Circle, ChevronRight } from "lucide-react";
import { cn } from "@/lib/utils";
import Link from "next/link";

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
}: StepIndicatorProps) {
  return (
    <div className="flex items-center gap-2 mb-4 p-3 bg-muted/30 rounded-lg overflow-x-auto">
      {steps.map((step, index) => (
        <div key={step.number} className="flex items-center">
          <Link 
            href={step.href}
            className={cn(
              "flex items-center gap-1.5 px-2 py-1 rounded text-xs whitespace-nowrap transition-colors",
              step.status === "current" && "bg-primary text-primary-foreground",
              step.status === "completed" && "text-green-600 hover:bg-green-50",
              step.status === "pending" && "text-muted-foreground hover:bg-muted",
              step.status === "optional" && "text-muted-foreground hover:bg-muted"
            )}
          >
            {step.status === "completed" ? (
              <CheckCircle2 className="h-3.5 w-3.5" />
            ) : step.status === "current" ? (
              <span className="w-4 h-4 rounded-full bg-primary-foreground text-primary text-[10px] flex items-center justify-center font-bold">
                {step.number}
              </span>
            ) : (
              <Circle className="h-3.5 w-3.5" />
            )}
            <span className="font-medium">{step.title}</span>
            {step.status === "optional" && (
              <Badge variant="outline" className="text-[10px] px-1 py-0 h-4">可选</Badge>
            )}
          </Link>
          {index < steps.length - 1 && (
            <ChevronRight className="h-3 w-3 mx-1 text-muted-foreground flex-shrink-0" />
          )}
        </div>
      ))}
    </div>
  );
}

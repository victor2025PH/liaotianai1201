"use client";

import React, { createContext, useContext, useState, useEffect, useCallback } from "react";
import { translations, Language, TranslationContent } from "./translations";

interface I18nContextType {
  language: Language;
  setLanguage: (lang: Language) => void;
  t: TranslationContent;
}

const I18nContext = createContext<I18nContextType | undefined>(undefined);

const STORAGE_KEY = "app-language";

// 验证语言代码是否有效
function isValidLanguage(lang: string | null): lang is Language {
  return lang === "zh-CN" || lang === "zh-TW" || lang === "en";
}

export function I18nProvider({ children }: { children: React.ReactNode }) {
  const [language, setLanguageState] = useState<Language>("zh-CN");
  const [mounted, setMounted] = useState(false);

  // 从 localStorage 读取语言设置
  useEffect(() => {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (isValidLanguage(stored)) {
      setLanguageState(stored);
    }
    setMounted(true);
  }, []);

  // 切换语言
  const setLanguage = useCallback((lang: Language) => {
    setLanguageState(lang);
    localStorage.setItem(STORAGE_KEY, lang);
    // 更新 HTML lang 属性
    if (lang === "zh-CN") {
      document.documentElement.lang = "zh-Hans";
    } else if (lang === "zh-TW") {
      document.documentElement.lang = "zh-Hant";
    } else {
      document.documentElement.lang = "en";
    }
  }, []);

  // 获取翻译（使用类型断言避免类型推断问题）
  const t = translations[language] as TranslationContent;

  // 防止 SSR 不匹配
  if (!mounted) {
    return (
      <I18nContext.Provider value={{ language: "zh-CN", setLanguage, t: translations["zh-CN"] as TranslationContent }}>
        {children}
      </I18nContext.Provider>
    );
  }

  return (
    <I18nContext.Provider value={{ language, setLanguage, t }}>
      {children}
    </I18nContext.Provider>
  );
}

export function useI18n() {
  const context = useContext(I18nContext);
  if (!context) {
    throw new Error("useI18n must be used within I18nProvider");
  }
  return context;
}

// 便捷 hook：只获取翻译
export function useTranslation() {
  const { t, language } = useI18n();
  return { t, language };
}

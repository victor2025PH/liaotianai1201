'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import DashboardStats from '@/components/DashboardStats';
import UsageChart from '@/components/UsageChart';
import RecentErrors from '@/components/RecentErrors';
import SessionList from '@/components/SessionList';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'https://aiadmin.usdt2026.cc';

export default function Home() {
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(false);
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-xl">加载中...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* 导航栏 */}
      <nav className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <h1 className="text-2xl font-bold text-gray-900">
                统一后台管理系统
              </h1>
            </div>
            <div className="flex items-center space-x-4">
              <Link
                href="/"
                className="text-gray-700 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium"
              >
                仪表盘
              </Link>
              <Link
                href="/sessions"
                className="text-gray-700 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium"
              >
                会话管理
              </Link>
              <Link
                href="/analytics"
                className="text-gray-700 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium"
              >
                数据分析
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* 主内容 */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* 统计卡片 */}
        <DashboardStats />

        {/* 图表区域 */}
        <div className="mt-8 grid grid-cols-1 lg:grid-cols-2 gap-6">
          <UsageChart />
          <RecentErrors />
        </div>

        {/* 会话列表 */}
        <div className="mt-8">
          <SessionList />
        </div>
      </main>
    </div>
  );
}


'use client';

import { useEffect, useState } from 'react';
import Navigation from '@/components/Navigation';
import DashboardStats from '@/components/DashboardStats';
import UsageChart from '@/components/UsageChart';
import RecentErrors from '@/components/RecentErrors';
import SessionList from '@/components/SessionList';
import ProviderComparison from '@/components/ProviderComparison';

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
      <Navigation />

      {/* 主内容 */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* 统计卡片 */}
        <DashboardStats />

        {/* 图表区域 */}
        <div className="mt-8 grid grid-cols-1 lg:grid-cols-2 gap-6">
          <UsageChart />
          <RecentErrors />
        </div>

        {/* 提供商对比 */}
        <div className="mt-8">
          <ProviderComparison />
        </div>

        {/* 会话列表 */}
        <div className="mt-8">
          <SessionList />
        </div>
      </main>
    </div>
  );
}


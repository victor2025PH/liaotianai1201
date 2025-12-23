'use client';

import { useEffect, useState } from 'react';
import Navigation from '@/components/Navigation';
import SitesOverview from '@/components/SitesOverview';
import TrafficStats from '@/components/TrafficStats';

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

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <h2 className="text-2xl font-bold mb-6">站点概览</h2>
        
        {/* 站点列表 */}
        <SitesOverview />

        {/* 访问统计 */}
        <div className="mt-8">
          <TrafficStats />
        </div>
      </main>
    </div>
  );
}


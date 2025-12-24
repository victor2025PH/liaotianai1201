'use client';

import { useEffect, useState } from 'react';
import axios from 'axios';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'https://aiadmin.usdt2026.cc';

interface ProviderStat {
  provider: string;
  total_requests: number;
  total_tokens: number;
  total_cost: number;
  success_rate: number;
  avg_tokens_per_request: number;
}

export default function ProviderComparison() {
  const [stats, setStats] = useState<ProviderStat[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchStats();
    // 每 60 秒自动刷新
    const interval = setInterval(fetchStats, 60000);
    return () => clearInterval(interval);
  }, []);

  const fetchStats = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/v1/ai-monitoring/providers?days=7`);
      setStats(response.data);
    } catch (err) {
      console.error('获取提供商统计失败:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-bold mb-4">提供商对比</h2>
        <div className="h-64 flex items-center justify-center">
          <div className="text-gray-500">加载中...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h2 className="text-xl font-bold mb-4">提供商对比（最近 7 天）</h2>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={stats}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="provider" />
          <YAxis yAxisId="left" />
          <YAxis yAxisId="right" orientation="right" />
          <Tooltip />
          <Legend />
          <Bar yAxisId="left" dataKey="total_requests" fill="#3b82f6" name="请求数" />
          <Bar yAxisId="right" dataKey="total_cost" fill="#10b981" name="成本 (USD)" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}


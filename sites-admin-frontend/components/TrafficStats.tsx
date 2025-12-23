'use client';

import { useEffect, useState } from 'react';
import axios from 'axios';
import {
  LineChart,
  Line,
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

export default function TrafficStats() {
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // TODO: 实现数据获取
    setLoading(false);
  }, []);

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-xl font-bold mb-4">访问统计</h3>
        <div className="text-gray-500">加载中...</div>
      </div>
    );
  }

  // 临时数据
  const pvData = [
    { date: '12/18', aizkw: 1200, hongbao: 800, tgmini: 600 },
    { date: '12/19', aizkw: 1500, hongbao: 900, tgmini: 700 },
    { date: '12/20', aizkw: 1800, hongbao: 1000, tgmini: 800 },
    { date: '12/21', aizkw: 2000, hongbao: 1100, tgmini: 900 },
    { date: '12/22', aizkw: 2200, hongbao: 1200, tgmini: 1000 },
    { date: '12/23', aizkw: 2400, hongbao: 1300, tgmini: 1100 },
    { date: '12/24', aizkw: 2600, hongbao: 1400, tgmini: 1200 },
  ];

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-xl font-bold mb-4">访问统计（最近 7 天）</h3>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* PV 趋势 */}
        <div>
          <h4 className="text-sm font-medium text-gray-700 mb-2">页面访问量 (PV)</h4>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={pvData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="aizkw" stroke="#3b82f6" name="智控王" />
              <Line type="monotone" dataKey="hongbao" stroke="#10b981" name="红包游戏" />
              <Line type="monotone" dataKey="tgmini" stroke="#f59e0b" name="TON Mini App" />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* 站点对比 */}
        <div>
          <h4 className="text-sm font-medium text-gray-700 mb-2">站点对比</h4>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={[
              { name: '智控王', pv: 2600, uv: 1200 },
              { name: '红包游戏', pv: 1400, uv: 800 },
              { name: 'TON Mini App', pv: 1200, uv: 600 },
            ]}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="pv" fill="#3b82f6" name="PV" />
              <Bar dataKey="uv" fill="#10b981" name="UV" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}


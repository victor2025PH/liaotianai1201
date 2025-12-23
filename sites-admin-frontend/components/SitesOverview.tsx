'use client';

import { useEffect, useState } from 'react';
import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'https://aiadmin.usdt2026.cc';

interface Site {
  id: number;
  name: string;
  url: string;
  site_type: string;
  status: string;
  stats: {
    today_pv: number;
    today_uv: number;
    today_conversations: number;
  };
}

export default function SitesOverview() {
  const [sites, setSites] = useState<Site[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchSites();
  }, []);

  const fetchSites = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/v1/sites`);
      setSites(response.data.items || []);
      setError(null);
    } catch (err: any) {
      console.error('获取站点列表失败:', err);
      setError(err.message || '获取站点列表失败');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="text-gray-500">加载中...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-800">错误: {error}</p>
        <button
          onClick={fetchSites}
          className="mt-2 text-red-600 hover:text-red-800 underline"
        >
          重试
        </button>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
      {sites.map((site) => (
        <div key={site.id} className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">{site.name}</h3>
            <span className={`px-2 py-1 rounded text-xs ${
              site.status === 'active' 
                ? 'bg-green-100 text-green-800' 
                : 'bg-gray-100 text-gray-800'
            }`}>
              {site.status === 'active' ? '在线' : '离线'}
            </span>
          </div>
          
          <p className="text-sm text-gray-600 mb-4">
            <a 
              href={site.url} 
              target="_blank" 
              rel="noopener noreferrer"
              className="text-blue-600 hover:text-blue-800"
            >
              {site.url}
            </a>
          </p>

          <div className="grid grid-cols-3 gap-4 pt-4 border-t">
            <div>
              <p className="text-xs text-gray-500">今日 PV</p>
              <p className="text-lg font-bold text-gray-900">
                {site.stats.today_pv.toLocaleString()}
              </p>
            </div>
            <div>
              <p className="text-xs text-gray-500">今日 UV</p>
              <p className="text-lg font-bold text-gray-900">
                {site.stats.today_uv.toLocaleString()}
              </p>
            </div>
            <div>
              <p className="text-xs text-gray-500">对话数</p>
              <p className="text-lg font-bold text-gray-900">
                {site.stats.today_conversations.toLocaleString()}
              </p>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}


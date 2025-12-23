'use client';

import { useEffect, useState } from 'react';
import axios from 'axios';
import { format } from 'date-fns';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'https://aiadmin.usdt2026.cc';

interface SessionStat {
  session_id: string;
  total_requests: number;
  total_tokens: number;
  total_cost: number;
  requests_by_provider: Record<string, number>;
  requests_by_model: Record<string, number>;
  first_request: string | null;
  last_request: string | null;
}

interface ActiveSession {
  session_id: string;
  request_count: number;
  total_tokens: number;
  total_cost: number;
  first_request: string | null;
  last_request: string | null;
}

export default function SessionList() {
  const [activeSessions, setActiveSessions] = useState<ActiveSession[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedSession, setSelectedSession] = useState<string | null>(null);
  const [sessionDetails, setSessionDetails] = useState<SessionStat | null>(null);

  useEffect(() => {
    fetchActiveSessions();
  }, []);

  const fetchActiveSessions = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/v1/ai-monitoring/sessions/active?days=7&limit=50`);
      setActiveSessions(response.data.sessions || []);
    } catch (err) {
      console.error('获取活跃会话失败:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchSessionDetails = async (sessionId: string) => {
    try {
      const response = await axios.get(
        `${API_BASE_URL}/api/v1/ai-monitoring/session/${sessionId}?days=30`
      );
      setSessionDetails(response.data);
      setSelectedSession(sessionId);
    } catch (err) {
      console.error('获取会话详情失败:', err);
    }
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-bold mb-4">活跃会话</h2>
        <div className="text-gray-500">加载中...</div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h2 className="text-xl font-bold mb-4">会话管理</h2>
      
      <div className="mb-4">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          查询会话统计
        </label>
        <div className="flex space-x-2">
          <input
            type="text"
            placeholder="输入会话 ID"
            className="flex-1 px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            onKeyPress={(e) => {
              if (e.key === 'Enter') {
                const input = e.currentTarget as HTMLInputElement;
                if (input.value.trim()) {
                  fetchSessionDetails(input.value.trim());
                }
              }
            }}
          />
          <button
            onClick={() => {
              const input = document.querySelector('input[type="text"]') as HTMLInputElement;
              if (input?.value.trim()) {
                fetchSessionDetails(input.value.trim());
              }
            }}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
          >
            查询
          </button>
        </div>
      </div>

      {sessionDetails && (
        <div className="mt-6 border-t pt-6">
          <h3 className="text-lg font-semibold mb-4">会话详情</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <p className="text-sm text-gray-600">会话 ID</p>
              <p className="text-sm font-mono text-gray-900 break-all">
                {sessionDetails.session_id}
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-600">总请求数</p>
              <p className="text-lg font-bold">{sessionDetails.total_requests}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">总 Token</p>
              <p className="text-lg font-bold">{sessionDetails.total_tokens.toLocaleString()}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">总成本</p>
              <p className="text-lg font-bold">${sessionDetails.total_cost.toFixed(4)}</p>
            </div>
          </div>

          {sessionDetails.first_request && (
            <div className="mt-4 grid grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-gray-600">首次请求</p>
                <p className="text-sm">
                  {format(new Date(sessionDetails.first_request), 'yyyy-MM-dd HH:mm:ss')}
                </p>
              </div>
              {sessionDetails.last_request && (
                <div>
                  <p className="text-sm text-gray-600">最后请求</p>
                  <p className="text-sm">
                    {format(new Date(sessionDetails.last_request), 'yyyy-MM-dd HH:mm:ss')}
                  </p>
                </div>
              )}
            </div>
          )}

          <div className="mt-4">
            <p className="text-sm font-medium text-gray-700 mb-2">按提供商分布</p>
            <div className="flex flex-wrap gap-2">
              {Object.entries(sessionDetails.requests_by_provider).map(([provider, count]) => (
                <span
                  key={provider}
                  className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm"
                >
                  {provider}: {count}
                </span>
              ))}
            </div>
          </div>

          <div className="mt-4">
            <p className="text-sm font-medium text-gray-700 mb-2">按模型分布</p>
            <div className="flex flex-wrap gap-2">
              {Object.entries(sessionDetails.requests_by_model).map(([model, count]) => (
                <span
                  key={model}
                  className="px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm"
                >
                  {model}: {count}
                </span>
              ))}
            </div>
          </div>
        </div>
      )}

      {!sessionDetails && (
        <div className="text-center text-gray-500 py-8">
          <p>输入会话 ID 查询统计信息</p>
        </div>
      )}
    </div>
  );
}


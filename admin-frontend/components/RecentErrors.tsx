'use client';

import { useEffect, useState } from 'react';
import axios from 'axios';
import { format } from 'date-fns';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'https://aiadmin.usdt2026.cc';

interface ErrorLog {
  id: number;
  provider: string;
  model: string;
  site_domain: string;
  error_message: string;
  created_at: string;
}

export default function RecentErrors() {
  const [errors, setErrors] = useState<ErrorLog[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchErrors();
  }, []);

  const fetchErrors = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/v1/ai-monitoring/recent-errors?limit=10`);
      setErrors(response.data);
    } catch (err) {
      console.error('获取错误日志失败:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-bold mb-4">最近错误</h2>
        <div className="text-gray-500">加载中...</div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h2 className="text-xl font-bold mb-4">最近错误</h2>
      <div className="space-y-3 max-h-64 overflow-y-auto">
        {errors.length === 0 ? (
          <div className="text-center text-gray-500 py-8">
            <svg
              className="mx-auto h-12 w-12 text-gray-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            <p className="mt-2">暂无错误</p>
          </div>
        ) : (
          errors.map((error) => (
            <div
              key={error.id}
              className="border-l-4 border-red-500 bg-red-50 p-3 rounded"
            >
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <div className="flex items-center space-x-2">
                    <span className="text-sm font-medium text-red-800">
                      {error.provider} / {error.model}
                    </span>
                    {error.site_domain && (
                      <span className="text-xs text-gray-600">
                        ({error.site_domain})
                      </span>
                    )}
                  </div>
                  <p className="text-sm text-red-700 mt-1">
                    {error.error_message?.substring(0, 100)}
                    {error.error_message && error.error_message.length > 100 && '...'}
                  </p>
                </div>
                <span className="text-xs text-gray-500 ml-2">
                  {format(new Date(error.created_at), 'MM/dd HH:mm')}
                </span>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}


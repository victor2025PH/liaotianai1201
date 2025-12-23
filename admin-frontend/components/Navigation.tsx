'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';

export default function Navigation() {
  const pathname = usePathname();
  
  return (
    <nav className="bg-white shadow-sm border-b">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex items-center">
            <h1 className="text-2xl font-bold text-gray-900">
              AI 使用监控系统
            </h1>
          </div>
          <div className="flex items-center space-x-4">
            <Link
              href="/"
              className={`px-3 py-2 rounded-md text-sm font-medium ${
                pathname === '/' 
                  ? 'bg-blue-100 text-blue-700' 
                  : 'text-gray-700 hover:text-gray-900'
              }`}
            >
              仪表盘
            </Link>
            <Link
              href="/sessions"
              className={`px-3 py-2 rounded-md text-sm font-medium ${
                pathname === '/sessions' 
                  ? 'bg-blue-100 text-blue-700' 
                  : 'text-gray-700 hover:text-gray-900'
              }`}
            >
              会话管理
            </Link>
            <Link
              href="/analytics"
              className={`px-3 py-2 rounded-md text-sm font-medium ${
                pathname === '/analytics' 
                  ? 'bg-blue-100 text-blue-700' 
                  : 'text-gray-700 hover:text-gray-900'
              }`}
            >
              数据分析
            </Link>
          </div>
        </div>
      </div>
    </nav>
  );
}


#!/usr/bin/env node
/**
 * API 配置一键应用脚本
 * 
 * 使用方法:
 *   node scripts/apply-api-config.js dev    # 切换到开发环境
 *   node scripts/apply-api-config.js prod   # 切换到生产环境
 */

const fs = require('fs');
const path = require('path');

const ENV = process.argv[2] || 'dev';
const isDev = ENV === 'dev';

// 配置映射
const configs = {
  dev: {
    apiBase: 'http://localhost:8000/api/v1',
    apiUrl: 'http://localhost:8000/api/v1/group-ai',
    wsUrl: 'ws://localhost:8000/api/v1/notifications/ws',
    errorMsg: '無法連接到後端服務，請檢查服務是否運行（http://localhost:8000）'
  },
  prod: {
    apiBase: 'http://jblt.usdt2026.cc/api/v1',
    apiUrl: 'http://jblt.usdt2026.cc/api/v1/group-ai',
    wsUrl: 'ws://jblt.usdt2026.cc/api/v1/notifications/ws',
    errorMsg: '無法連接到後端服務，請檢查網絡連接'
  }
};

const config = configs[ENV];

// 文件替换规则
const fileRules = [
  // API 基础配置
  {
    file: 'src/lib/api-client.ts',
    rules: [
      {
        from: /const API_BASE_URL = process\.env\.NEXT_PUBLIC_API_BASE_URL \|\| "http:\/\/[^"]+"/,
        to: `const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "${config.apiBase}"`
      }
    ]
  },
  {
    file: 'src/lib/api/auth.ts',
    rules: [
      {
        from: /const API_BASE = process\.env\.NEXT_PUBLIC_API_[A-Z_]+ \|\| "http:\/\/[^"]+"/,
        to: `const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "${config.apiBase}"`
      },
      {
        from: /throw new Error\("無法連接到後端服務[^"]+"\)/,
        to: `throw new Error("${config.errorMsg}")`
      }
    ]
  },
  {
    file: 'src/lib/api/notifications.ts',
    rules: [
      {
        from: /const API_BASE = process\.env\.NEXT_PUBLIC_API_[A-Z_]+ \|\| "http:\/\/[^"]+"/,
        to: `const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "${config.apiBase}"`
      }
    ]
  },
  {
    file: 'src/lib/api/users.ts',
    rules: [
      {
        from: /const API_BASE = process\.env\.NEXT_PUBLIC_API_[A-Z_]+ \|\| "http:\/\/[^"]+"/,
        to: `const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "${config.apiBase}"`
      }
    ]
  },
  {
    file: 'src/lib/api/servers.ts',
    rules: [
      {
        from: /const API_BASE = process\.env\.NEXT_PUBLIC_API_BASE_URL \|\| "http:\/\/[^"]+";/,
        to: `const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "${config.apiBase}";`
      }
    ]
  },
  {
    file: 'src/lib/api/permissions.ts',
    rules: [
      {
        from: /const API_BASE = process\.env\.NEXT_PUBLIC_API_[A-Z_]+ \|\| "http:\/\/[^"]+"/,
        to: `const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "${config.apiBase}"`
      }
    ]
  },
  {
    file: 'src/lib/api/roles.ts',
    rules: [
      {
        from: /const API_BASE = process\.env\.NEXT_PUBLIC_API_[A-Z_]+ \|\| "http:\/\/[^"]+"/,
        to: `const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "${config.apiBase}"`
      }
    ]
  },
  {
    file: 'src/lib/api/audit-logs.ts',
    rules: [
      {
        from: /const API_BASE = process\.env\.NEXT_PUBLIC_API_[A-Z_]+ \|\| "http:\/\/[^"]+"/,
        to: `const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "${config.apiBase}"`
      }
    ]
  },
  {
    file: 'src/lib/api/telegram-registration.ts',
    rules: [
      {
        from: /const API_BASE = process\.env\.NEXT_PUBLIC_API_BASE_URL \|\| "http:\/\/[^"]+";/,
        to: `const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "${config.apiBase}";`
      }
    ]
  },
  {
    file: 'src/lib/api/group-ai.ts',
    rules: [
      {
        from: /const API_BASE = process\.env\.NEXT_PUBLIC_API_URL \|\| "http:\/\/[^"]+"/,
        to: `const API_BASE = process.env.NEXT_PUBLIC_API_URL || "${config.apiUrl}"`
      }
    ]
  },
  {
    file: 'src/lib/api/user-roles.ts',
    rules: [
      {
        from: /const API_BASE = process\.env\.NEXT_PUBLIC_API_[A-Z_]+ \|\| "http:\/\/[^"]+"/,
        to: `const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "${config.apiBase}"`
      }
    ]
  },
  {
    file: 'src/hooks/useAccountsQuery.ts',
    rules: [
      {
        from: /const API_BASE = process\.env\.NEXT_PUBLIC_API_URL \|\| "http:\/\/[^"]+";/,
        to: `const API_BASE = process.env.NEXT_PUBLIC_API_URL || "${config.apiUrl}";`
      }
    ]
  },
  {
    file: 'src/components/notification-center.tsx',
    rules: [
      {
        from: /process\.env\.NEXT_PUBLIC_API_[A-Z_]+ \|\| "http:\/\/[^"]+"/,
        to: `process.env.NEXT_PUBLIC_API_BASE_URL || "${config.apiBase}"`
      },
      {
        from: /"ws:\/\/[^"]+"/,
        to: `"${config.wsUrl}"`
      }
    ]
  }
];

// 执行替换
function applyRules() {
  const projectRoot = path.resolve(__dirname, '..');
  let totalFiles = 0;
  let totalChanges = 0;

  console.log(`\n🔄 切换到 ${isDev ? '开发' : '生产'}环境配置...\n`);

  fileRules.forEach(({ file, rules }) => {
    const filePath = path.join(projectRoot, file);
    
    if (!fs.existsSync(filePath)) {
      console.log(`⚠️  文件不存在: ${file}`);
      return;
    }

    let content = fs.readFileSync(filePath, 'utf-8');
    let changed = false;

    rules.forEach(({ from, to }) => {
      if (from.test(content)) {
        content = content.replace(from, to);
        changed = true;
        totalChanges++;
      }
    });

    if (changed) {
      fs.writeFileSync(filePath, content, 'utf-8');
      console.log(`✅ ${file}`);
      totalFiles++;
    } else {
      console.log(`⏭️  ${file} (无需修改)`);
    }
  });

  console.log(`\n✨ 完成! 修改了 ${totalFiles} 个文件，共 ${totalChanges} 处更改\n`);
}

// 运行
if (ENV !== 'dev' && ENV !== 'prod') {
  console.error('❌ 错误: 请指定环境 (dev 或 prod)');
  console.log('使用方法: node scripts/apply-api-config.js [dev|prod]');
  process.exit(1);
}

applyRules();











import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Enable standalone output for Docker deployment
  output: "standalone",
  
  // 生產優化
  compress: true,
  productionBrowserSourceMaps: false,
  
  // 性能優化
  experimental: {
    // 優化打包大小
    optimizePackageImports: [
      "lucide-react",
      "@radix-ui/react-icons",
      "recharts",
      "@radix-ui/react-dialog",
      "@radix-ui/react-select",
      "@radix-ui/react-dropdown-menu",
    ],
    // 優化服務器組件
    serverActions: {
      bodySizeLimit: "2mb",
    },
  },
  
  // 圖片優化
  images: {
    formats: ["image/avif", "image/webp"],
    minimumCacheTTL: 60 * 60 * 24 * 30, // 30 天緩存
    deviceSizes: [640, 750, 828, 1080, 1200, 1920, 2048, 3840],
    imageSizes: [16, 32, 48, 64, 96, 128, 256, 384],
    dangerouslyAllowSVG: true,
    contentSecurityPolicy: "default-src 'self'; script-src 'none'; sandbox;",
    unoptimized: true, // 关键：开启此项以避免在无 sharp 环境下报错
  },
  
  // 編譯優化
  compiler: {
    // 移除 console.log（生產環境）
    removeConsole: process.env.NODE_ENV === "production" ? {
      exclude: ["error", "warn"],
    } : false,
  },
  
  // 頁面預載
  poweredByHeader: false,
  
  // 重定向優化（移除末尾斜杠）
  trailingSlash: false,
  
  // 確保 standalone 模式正確生成所有必需文件
  // 這可以解決 routes.js 缺失的問題
  webpack: (config, { isServer }) => {
    if (isServer) {
      // 確保服務器端構建包含所有必需文件
      config.resolve.fallback = {
        ...config.resolve.fallback,
        fs: false,
        net: false,
        tls: false,
      };
    }
    return config;
  },
};

export default nextConfig;
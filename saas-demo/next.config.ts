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
    ],
  },
  
  // 圖片優化
  images: {
    formats: ["image/avif", "image/webp"],
    minimumCacheTTL: 60 * 60 * 24 * 30, // 30 天緩存
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
};

export default nextConfig;

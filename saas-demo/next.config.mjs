/** @type {import('next').NextConfig} */
const nextConfig = {
  // ❌ 已禁用 Standalone 模式，使用 Standard 模式（避免 MODULE_NOT_FOUND 错误）
  // output: "standalone",
  
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
};

export default nextConfig;


import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Enable standalone output for Docker deployment
  output: "standalone",
  
  // Optional: Optimize for production
  compress: true,
  
  // Optional: Disable source maps in production (reduces image size)
  productionBrowserSourceMaps: false,
};

export default nextConfig;

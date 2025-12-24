/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  env: {
    API_BASE_URL: process.env.API_BASE_URL || 'https://aiadmin.usdt2026.cc',
  },
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: `${process.env.API_BASE_URL || 'https://aiadmin.usdt2026.cc'}/api/v1/:path*`,
      },
    ];
  },
};

module.exports = nextConfig;


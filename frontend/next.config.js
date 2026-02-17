/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  typescript: {
    // ⚠️ Production 빌드 시 타입 에러 무시 (배포 후 수정)
    ignoreBuildErrors: true,
  },
  eslint: {
    // ⚠️ Production 빌드 시 ESLint 에러 무시 (배포 후 수정)
    ignoreDuringBuilds: true,
  },
  // Docker 컨테이너 배포용 standalone 빌드
  output: 'standalone',
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  },
  images: {
    remotePatterns: [
      {
        protocol: 'http',
        hostname: 'localhost',
        port: '8000',
        pathname: '/**',
      },
      {
        protocol: 'https',
        hostname: '**',
      },
    ],
  },
}

module.exports = nextConfig

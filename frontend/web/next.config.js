/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  images: {
    unoptimized: false,
  },
  typescript: {
    strictNullChecks: true,
  },
}

module.exports = nextConfig

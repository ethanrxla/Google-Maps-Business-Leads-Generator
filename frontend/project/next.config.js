/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'export',
  images: { unoptimized: true },
  turbopack: {
    root: '.',
  },
};

module.exports = nextConfig;

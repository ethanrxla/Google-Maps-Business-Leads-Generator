/** @type {import('next').NextConfig} */
const nextConfig = {
  // output: 'export',  // disabled for dev server; re-enable for static builds
  images: { unoptimized: true },
  turbopack: {
    root: '.',
  },
};

module.exports = nextConfig;

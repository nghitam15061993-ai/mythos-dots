/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: "export",          // static export → host được trên IPFS
  images: { unoptimized: true },
  trailingSlash: true,       // hợp gateway IPFS (dir/index.html)
};
export default nextConfig;

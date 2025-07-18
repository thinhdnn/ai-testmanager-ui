import type { NextConfig } from "next";

const config: NextConfig = {
  webpack: (config) => {
    config.resolve.extensions = ['.tsx', '.ts', '.js', '.jsx']
    return config
  }
};

export default config;

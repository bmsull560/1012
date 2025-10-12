// frontend/next.config.js

/**
 * Next.js configuration file.
 *
 * This file is used to configure Next.js for the application.
 *
 * @see https://nextjs.org/docs/api-reference/next.config.js/introduction
 */

module.exports = {
  // Target serverless deployment
  target: 'serverless',

  // Enable experimental features
  experimental: {
    // Enable React Concurrent Mode
    concurrentFeatures: true,
  },

  // Configure Next.js to use TypeScript
  typescript: {
    // Enable TypeScript type checking
    ignoreBuildErrors: true,
  },

  // Configure Next.js to use Tailwind CSS
  tailwindcss: {
    // Enable Tailwind CSS
    enabled: true,
  },

  // Configure Next.js to use PostCSS
  postcss: {
    // Enable PostCSS
    enabled: true,
  },

  // Configure Next.js to use ESLint
  eslint: {
    // Enable ESLint
    enabled: true,
  },

  // Configure Next.js to use PWA
  pwa: {
    // Enable PWA
    enabled: true,
    // Configure PWA manifest
    manifest: {
      name: 'ValueVerse B2B Value Realization Platform',
      short_name: 'ValueVerse',
      description: 'ValueVerse B2B Value Realization Platform',
      theme_color: '#000',
      background_color: '#fff',
      display: 'standalone',
      icons: [
        {
          src: '/favicon.ico',
          sizes: '192x192',
          type: 'image/png',
        },
      ],
    },
  },

  // Configure Next.js to use internationalization
  i18n: {
    // Enable internationalization
    enabled: true,
    // Configure locales
    locales: ['en-US'],
    // Configure default locale
    defaultLocale: 'en-US',
  },

  // Configure Next.js to use redirects
  redirects: async () => {
    // Configure redirects
    return [
      {
        source: '/old-path',
        destination: '/new-path',
        permanent: true,
      },
    ];
  },

  // Configure Next.js to use rewrites
  rewrites: async () => {
    // Configure rewrites
    return [
      {
        source: '/api/:path*',
        destination: '/api/:path*',
      },
    ];
  },

  // Configure Next.js to use headers
  headers: async () => {
    // Configure headers
    return [
      {
        source: '/:path*',
        headers: [
          {
            key: 'X-Frame-Options',
            value: 'SAMEORIGIN',
          },
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff',
          },
          {
            key: 'X-XSS-Protection',
            value: '1; mode=block',
          },
          {
            key: 'Content-Security-Policy',
            value: "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';",
          },
        ],
      },
    ];
  },
};
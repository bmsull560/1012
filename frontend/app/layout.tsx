import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import ErrorBoundary from '@/components/common/ErrorBoundary'
import { MonitoringProvider } from '@/components/providers/MonitoringProvider'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'ValueVerse Platform',
  description: 'Enterprise B2B Value Realization Platform',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <MonitoringProvider>
          <ErrorBoundary
            fallback={
              <div className="flex min-h-screen flex-col items-center justify-center gap-4 bg-slate-50 p-6 text-center">
                <h1 className="text-2xl font-semibold text-slate-900">We're working on it</h1>
                <p className="max-w-md text-sm text-slate-600">
                  An unexpected issue prevented the application from loading. Please refresh the page or try again later.
                </p>
                <button
                  type="button"
                  className="rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white shadow-sm transition hover:bg-slate-700"
                  onClick={() => window.location.reload()}
                >
                  Refresh
                </button>
              </div>
            }
          >
            {children}
          </ErrorBoundary>
        </MonitoringProvider>
      </body>
    </html>
  )
}

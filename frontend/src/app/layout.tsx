import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'ValueVerse - B2B Value Realization Platform',
  description: 'AI-powered B2B value realization operating system',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>
        <div className="min-h-screen bg-gray-50">
          {children}
        </div>
      </body>
    </html>
  )
}

import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import { DesignSystemProvider } from '@/design-system/DesignSystemProvider'
import { lightTokens } from '@/design-system/tokens'

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
        <DesignSystemProvider tokens={lightTokens}>{children}</DesignSystemProvider>
      </body>
    </html>
  )
}

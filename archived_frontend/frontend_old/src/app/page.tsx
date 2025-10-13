'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'

export default function Home() {
  const router = useRouter()
  
  useEffect(() => {
    // Redirect to the enterprise workspace
    router.push('/workspace')
  }, [router])
  
  return (
    <div className="flex flex-col items-center justify-center min-h-screen py-2">
      <main className="flex flex-col items-center justify-center w-full flex-1 px-20 text-center">
        <h1 className="text-6xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent mb-4">
          ValueVerse
        </h1>
        <p className="text-2xl text-gray-700 mb-8">
          B2B Value Realization Operating System
        </p>
        <p className="text-lg text-gray-600">
          Redirecting to workspace...
        </p>
      </main>
    </div>
  );
}

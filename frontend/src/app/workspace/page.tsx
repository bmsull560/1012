'use client'

import React from 'react'

export default function SimpleWorkspacePage() {
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="px-6 py-4 flex items-center justify-between">
          <h1 className="text-2xl font-bold text-blue-600">ValueVerse Enterprise</h1>
          <div className="flex gap-2">
            <button className="px-3 py-1 bg-blue-600 text-white rounded">Beginner</button>
            <button className="px-3 py-1 border rounded">Intermediate</button>
            <button className="px-3 py-1 border rounded">Expert</button>
          </div>
        </div>
      </div>

      {/* Main Content - Split View */}
      <div className="flex h-[calc(100vh-64px)]">
        {/* Left Panel - AI Chat */}
        <div className="w-1/2 bg-white border-r">
          <div className="p-4 bg-blue-50 border-b">
            <h2 className="font-semibold">AI Assistant</h2>
            <p className="text-sm text-gray-600">Conversational Intelligence</p>
          </div>
          <div className="p-4 space-y-4">
            <div className="bg-gray-100 rounded-lg p-3">
              <p className="text-sm">Welcome to ValueVerse! I'm orchestrating four specialized agents to help you realize customer value.</p>
            </div>
            <div className="bg-blue-100 rounded-lg p-3">
              <p className="text-sm">I've analyzed your value pipeline and identified 3 high-impact opportunities totaling $4.2M.</p>
            </div>
          </div>
          <div className="absolute bottom-0 left-0 w-1/2 p-4 border-t bg-white">
            <input 
              type="text" 
              placeholder="Ask me about customer value..."
              className="w-full p-2 border rounded"
            />
          </div>
        </div>

        {/* Right Panel - Value Canvas */}
        <div className="w-1/2 bg-gray-50">
          <div className="p-4 bg-purple-50 border-b">
            <h2 className="font-semibold">Value Canvas</h2>
            <p className="text-sm text-gray-600">Living Value Graph</p>
          </div>
          
          {/* Simple Graph Visualization */}
          <div className="relative h-full p-8">
            {/* Value Nodes */}
            <div className="absolute top-20 left-20 bg-blue-500 text-white rounded-full p-4 shadow-lg">
              <div className="text-center">
                <div className="font-bold">$2.3M</div>
                <div className="text-xs">Supply Chain</div>
              </div>
            </div>
            
            <div className="absolute top-20 right-20 bg-green-500 text-white rounded-full p-4 shadow-lg">
              <div className="text-center">
                <div className="font-bold">$0.75M</div>
                <div className="text-xs">Q1 Cost</div>
              </div>
            </div>
            
            <div className="absolute bottom-40 left-20 bg-amber-500 text-white rounded-full p-4 shadow-lg">
              <div className="text-center">
                <div className="font-bold">$1.2M</div>
                <div className="text-xs">Onboarding</div>
              </div>
            </div>
            
            <div className="absolute bottom-40 right-20 bg-purple-500 text-white rounded-full p-4 shadow-lg">
              <div className="text-center">
                <div className="font-bold">$4.1M</div>
                <div className="text-xs">EMEA</div>
              </div>
            </div>

            {/* Center text */}
            <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 text-center">
              <h3 className="text-xl font-semibold text-gray-700">Living Value Graph</h3>
              <p className="text-gray-500">$12.4M Total Pipeline</p>
            </div>

            {/* Legend */}
            <div className="absolute bottom-4 left-4 bg-white rounded p-3 shadow">
              <div className="text-xs space-y-1">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
                  <span>Hypothesis</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                  <span>Commitment</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 bg-amber-500 rounded-full"></div>
                  <span>Realization</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 bg-purple-500 rounded-full"></div>
                  <span>Amplification</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Bottom Status Bar */}
      <div className="fixed bottom-0 left-0 right-0 bg-white border-t px-6 py-2">
        <div className="flex items-center justify-between text-sm">
          <span className="text-green-600">● 4 Agents Active</span>
          <span>Pipeline: $12.4M | Realized: $2.7M | At Risk: $0.5M</span>
        </div>
      </div>
    </div>
  )
}

'use client'

import React, { useState, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  PanelLeft, 
  PanelRight, 
  Maximize2, 
  Minimize2,
  Brain,
  Network,
  MessageSquare,
  Sparkles
} from 'lucide-react'
import { cn } from '@/utils/cn'

interface DualBrainLayoutProps {
  leftPanel: React.ReactNode
  rightPanel: React.ReactNode
  className?: string
}

export function DualBrainLayout({ 
  leftPanel, 
  rightPanel, 
  className 
}: DualBrainLayoutProps) {
  const [leftWidth, setLeftWidth] = useState(40) // percentage
  const [isResizing, setIsResizing] = useState(false)
  const [leftCollapsed, setLeftCollapsed] = useState(false)
  const [rightCollapsed, setRightCollapsed] = useState(false)
  const [focusMode, setFocusMode] = useState<'none' | 'left' | 'right'>('none')

  const handleMouseDown = useCallback(() => {
    setIsResizing(true)
  }, [])

  const handleMouseMove = useCallback((e: MouseEvent) => {
    if (!isResizing) return
    
    const container = document.getElementById('dual-brain-container')
    if (!container) return
    
    const containerRect = container.getBoundingClientRect()
    const newLeftWidth = ((e.clientX - containerRect.left) / containerRect.width) * 100
    
    // Constrain between 20% and 80%
    setLeftWidth(Math.min(80, Math.max(20, newLeftWidth)))
  }, [isResizing])

  const handleMouseUp = useCallback(() => {
    setIsResizing(false)
  }, [])

  React.useEffect(() => {
    if (isResizing) {
      document.addEventListener('mousemove', handleMouseMove)
      document.addEventListener('mouseup', handleMouseUp)
      return () => {
        document.removeEventListener('mousemove', handleMouseMove)
        document.removeEventListener('mouseup', handleMouseUp)
      }
    }
  }, [isResizing, handleMouseMove, handleMouseUp])

  // Calculate actual widths based on collapse state
  const actualLeftWidth = leftCollapsed ? 0 : (rightCollapsed ? 100 : leftWidth)
  const actualRightWidth = rightCollapsed ? 0 : (leftCollapsed ? 100 : (100 - leftWidth))

  return (
    <div 
      id="dual-brain-container"
      className={cn(
        "flex h-full w-full relative overflow-hidden bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-950 dark:to-slate-900",
        className
      )}
    >
      {/* Left Brain - Conversational AI */}
      <AnimatePresence>
        {!leftCollapsed && (
          <motion.div
            initial={{ width: 0, opacity: 0 }}
            animate={{ 
              width: `${actualLeftWidth}%`, 
              opacity: 1 
            }}
            exit={{ width: 0, opacity: 0 }}
            transition={{ type: "spring", stiffness: 300, damping: 30 }}
            className="relative flex flex-col h-full border-r border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900"
          >
            {/* Left Brain Header */}
            <div className="flex items-center justify-between px-4 py-3 border-b border-slate-200 dark:border-slate-800 bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-950/20 dark:to-indigo-950/20">
              <div className="flex items-center gap-2">
                <div className="p-2 rounded-lg bg-blue-100 dark:bg-blue-900/50">
                  <Brain className="w-5 h-5 text-blue-600 dark:text-blue-400" />
                </div>
                <div>
                  <h2 className="text-sm font-semibold text-slate-900 dark:text-slate-100">
                    AI Assistant
                  </h2>
                  <p className="text-xs text-slate-500 dark:text-slate-400">
                    Conversational Intelligence
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-1">
                <button
                  onClick={() => setFocusMode(focusMode === 'left' ? 'none' : 'left')}
                  className="p-1.5 rounded-md hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
                  title="Focus mode"
                >
                  {focusMode === 'left' ? (
                    <Minimize2 className="w-4 h-4 text-slate-600 dark:text-slate-400" />
                  ) : (
                    <Maximize2 className="w-4 h-4 text-slate-600 dark:text-slate-400" />
                  )}
                </button>
                <button
                  onClick={() => setLeftCollapsed(true)}
                  className="p-1.5 rounded-md hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
                  title="Collapse panel"
                >
                  <PanelLeft className="w-4 h-4 text-slate-600 dark:text-slate-400" />
                </button>
              </div>
            </div>

            {/* Left Brain Content */}
            <div className="flex-1 overflow-hidden">
              {leftPanel}
            </div>

            {/* AI Status Indicator */}
            <div className="px-4 py-2 border-t border-slate-200 dark:border-slate-800 bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-950/20 dark:to-indigo-950/20">
              <div className="flex items-center gap-2">
                <div className="flex items-center gap-1">
                  <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
                  <span className="text-xs text-slate-600 dark:text-slate-400">
                    AI Active
                  </span>
                </div>
                <div className="flex items-center gap-1 ml-auto">
                  <Sparkles className="w-3 h-3 text-amber-500" />
                  <span className="text-xs text-slate-600 dark:text-slate-400">
                    4 agents orchestrating
                  </span>
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Resize Handle */}
      {!leftCollapsed && !rightCollapsed && (
        <div
          onMouseDown={handleMouseDown}
          className={cn(
            "w-1 hover:w-2 bg-slate-200 dark:bg-slate-700 hover:bg-blue-400 dark:hover:bg-blue-600 cursor-col-resize transition-all relative group",
            isResizing && "bg-blue-500 dark:bg-blue-500 w-2"
          )}
        >
          <div className="absolute inset-y-0 left-1/2 transform -translate-x-1/2 w-8 flex items-center justify-center">
            <div className="w-1 h-8 rounded-full bg-slate-400 dark:bg-slate-600 opacity-0 group-hover:opacity-100 transition-opacity" />
          </div>
        </div>
      )}

      {/* Right Brain - Interactive Canvas */}
      <AnimatePresence>
        {!rightCollapsed && (
          <motion.div
            initial={{ width: 0, opacity: 0 }}
            animate={{ 
              width: `${actualRightWidth}%`, 
              opacity: 1 
            }}
            exit={{ width: 0, opacity: 0 }}
            transition={{ type: "spring", stiffness: 300, damping: 30 }}
            className="relative flex flex-col h-full bg-slate-50 dark:bg-slate-950"
          >
            {/* Right Brain Header */}
            <div className="flex items-center justify-between px-4 py-3 border-b border-slate-200 dark:border-slate-800 bg-gradient-to-r from-purple-50 to-pink-50 dark:from-purple-950/20 dark:to-pink-950/20">
              <div className="flex items-center gap-2">
                <div className="p-2 rounded-lg bg-purple-100 dark:bg-purple-900/50">
                  <Network className="w-5 h-5 text-purple-600 dark:text-purple-400" />
                </div>
                <div>
                  <h2 className="text-sm font-semibold text-slate-900 dark:text-slate-100">
                    Value Canvas
                  </h2>
                  <p className="text-xs text-slate-500 dark:text-slate-400">
                    Living Value Graph
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-1">
                <button
                  onClick={() => setFocusMode(focusMode === 'right' ? 'none' : 'right')}
                  className="p-1.5 rounded-md hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
                  title="Focus mode"
                >
                  {focusMode === 'right' ? (
                    <Minimize2 className="w-4 h-4 text-slate-600 dark:text-slate-400" />
                  ) : (
                    <Maximize2 className="w-4 h-4 text-slate-600 dark:text-slate-400" />
                  )}
                </button>
                <button
                  onClick={() => setRightCollapsed(true)}
                  className="p-1.5 rounded-md hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
                  title="Collapse panel"
                >
                  <PanelRight className="w-4 h-4 text-slate-600 dark:text-slate-400" />
                </button>
              </div>
            </div>

            {/* Right Brain Content */}
            <div className="flex-1 overflow-hidden">
              {rightPanel}
            </div>

            {/* Canvas Status */}
            <div className="px-4 py-2 border-t border-slate-200 dark:border-slate-800 bg-gradient-to-r from-purple-50 to-pink-50 dark:from-purple-950/20 dark:to-pink-950/20">
              <div className="flex items-center gap-4 text-xs">
                <div className="flex items-center gap-1">
                  <div className="w-2 h-2 rounded-full bg-green-500" />
                  <span className="text-slate-600 dark:text-slate-400">
                    Real-time sync
                  </span>
                </div>
                <span className="text-slate-500 dark:text-slate-500">
                  12 nodes • 24 connections • $2.3M tracked value
                </span>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Collapsed Panel Toggles */}
      {leftCollapsed && (
        <motion.button
          initial={{ x: -20, opacity: 0 }}
          animate={{ x: 0, opacity: 1 }}
          onClick={() => setLeftCollapsed(false)}
          className="absolute left-2 top-1/2 -translate-y-1/2 p-2 rounded-lg bg-white dark:bg-slate-800 shadow-lg border border-slate-200 dark:border-slate-700 hover:shadow-xl transition-shadow z-10"
          title="Expand AI Assistant"
        >
          <MessageSquare className="w-5 h-5 text-blue-600 dark:text-blue-400" />
        </motion.button>
      )}

      {rightCollapsed && (
        <motion.button
          initial={{ x: 20, opacity: 0 }}
          animate={{ x: 0, opacity: 1 }}
          onClick={() => setRightCollapsed(false)}
          className="absolute right-2 top-1/2 -translate-y-1/2 p-2 rounded-lg bg-white dark:bg-slate-800 shadow-lg border border-slate-200 dark:border-slate-700 hover:shadow-xl transition-shadow z-10"
          title="Expand Value Canvas"
        >
          <Network className="w-5 h-5 text-purple-600 dark:text-purple-400" />
        </motion.button>
      )}

      {/* Focus Mode Overlay */}
      {focusMode !== 'none' && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="absolute inset-0 bg-black/20 pointer-events-none z-20"
        />
      )}
    </div>
  )
}

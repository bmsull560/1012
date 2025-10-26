"use client"

import React, { createContext, useContext, useMemo } from "react"
import { DesignTokens, lightTokens, tokensToCSSVariables } from "./tokens"

type DesignSystemContextValue = {
  tokens: DesignTokens
}

const DesignSystemContext = createContext<DesignSystemContextValue>({
  tokens: lightTokens,
})

export interface DesignSystemProviderProps {
  children: React.ReactNode
  tokens?: DesignTokens
}

export const DesignSystemProvider: React.FC<DesignSystemProviderProps> = ({
  children,
  tokens = lightTokens,
}) => {
  const cssVariables = useMemo(() => tokensToCSSVariables(tokens), [tokens])

  // Helper to convert cssVariables object to CSS string
  const cssVariablesString = useMemo(() => {
    return `:root { ${Object.entries(cssVariables).map(([key, value]) => `${key}: ${value};`).join(" ")} }`
  }, [cssVariables])

  return (
    <DesignSystemContext.Provider value={{ tokens }}>
      <style>{cssVariablesString}</style>
      {children}
    </DesignSystemContext.Provider>
  )
}

export const useDesignTokens = () => useContext(DesignSystemContext)

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

  return (
    <DesignSystemContext.Provider value={{ tokens }}>
      <div style={cssVariables}>{children}</div>
    </DesignSystemContext.Provider>
  )
}

export const useDesignTokens = () => useContext(DesignSystemContext)

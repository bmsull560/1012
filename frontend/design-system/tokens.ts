export type ColorTokens = {
  background: string
  foreground: string
  muted: string
  mutedForeground: string
  accent: string
  accentForeground: string
  primary: string
  primaryForeground: string
  secondary: string
  secondaryForeground: string
  destructive: string
  destructiveForeground: string
  border: string
  input: string
  ring: string
  card: string
  cardForeground: string
}

export type TypographyTokens = {
  fontFamily: string
  headings: {
    h1: string
    h2: string
    h3: string
    h4: string
    h5: string
    h6: string
  }
  body: string
  mono: string
}

export type RadiusTokens = {
  none: string
  sm: string
  md: string
  lg: string
  full: string
}

export type ShadowTokens = {
  sm: string
  md: string
  lg: string
  xl: string
}

export interface DesignTokens {
  colors: ColorTokens
  typography: TypographyTokens
  radius: RadiusTokens
  shadows: ShadowTokens
}

export const lightTokens: DesignTokens = {
  colors: {
    background: "0 0% 100%",
    foreground: "222.2 84% 4.9%",
    muted: "210 40% 96.1%",
    mutedForeground: "215.4 16.3% 46.9%",
    accent: "210 40% 96.1%",
    accentForeground: "222.2 47.4% 11.2%",
    primary: "221.2 83.2% 53.3%",
    primaryForeground: "210 40% 98%",
    secondary: "210 40% 96.1%",
    secondaryForeground: "222.2 47.4% 11.2%",
    destructive: "0 84.2% 60.2%",
    destructiveForeground: "0 0% 98%",
    border: "214.3 31.8% 91.4%",
    input: "214.3 31.8% 91.4%",
    ring: "221.2 83.2% 53.3%",
    card: "0 0% 100%",
    cardForeground: "222.2 84% 4.9%",
  },
  typography: {
    fontFamily: "'Inter', sans-serif",
    headings: {
      h1: "text-4xl font-bold tracking-tight",
      h2: "text-3xl font-semibold tracking-tight",
      h3: "text-2xl font-semibold tracking-tight",
      h4: "text-xl font-semibold tracking-tight",
      h5: "text-lg font-medium",
      h6: "text-base font-medium",
    },
    body: "text-base leading-relaxed text-foreground",
    mono: "'JetBrains Mono', monospace",
  },
  radius: {
    none: "0px",
    sm: "calc(var(--radius) - 4px)",
    md: "calc(var(--radius) - 2px)",
    lg: "var(--radius)",
    full: "9999px",
  },
  shadows: {
    sm: "0 1px 2px 0 rgba(15, 23, 42, 0.05)",
    md: "0 4px 6px -1px rgba(15, 23, 42, 0.1), 0 2px 4px -2px rgba(15, 23, 42, 0.1)",
    lg: "0 10px 15px -3px rgba(15, 23, 42, 0.1), 0 4px 6px -4px rgba(15, 23, 42, 0.1)",
    xl: "0 20px 25px -5px rgba(15, 23, 42, 0.1), 0 10px 10px -5px rgba(15, 23, 42, 0.04)",
  },
}

export const darkTokens: DesignTokens = {
  colors: {
    background: "240 10% 3.9%",
    foreground: "0 0% 98%",
    muted: "240 3.7% 15.9%",
    mutedForeground: "240 5% 64.9%",
    accent: "240 3.7% 15.9%",
    accentForeground: "0 0% 98%",
    primary: "222.2 47.4% 11.2%",
    primaryForeground: "210 40% 98%",
    secondary: "240 3.7% 15.9%",
    secondaryForeground: "0 0% 98%",
    destructive: "0 72.2% 50.6%",
    destructiveForeground: "0 0% 98%",
    border: "240 3.7% 15.9%",
    input: "240 3.7% 15.9%",
    ring: "263.4 70% 50.4%",
    card: "240 10% 3.9%",
    cardForeground: "0 0% 98%",
  },
  typography: lightTokens.typography,
  radius: lightTokens.radius,
  shadows: lightTokens.shadows,
}

export const tokensToCSSVariables = (tokens: DesignTokens) => {
  const entries: Record<string, string> = {
    "--background": tokens.colors.background,
    "--foreground": tokens.colors.foreground,
    "--muted": tokens.colors.muted,
    "--muted-foreground": tokens.colors.mutedForeground,
    "--accent": tokens.colors.accent,
    "--accent-foreground": tokens.colors.accentForeground,
    "--primary": tokens.colors.primary,
    "--primary-foreground": tokens.colors.primaryForeground,
    "--secondary": tokens.colors.secondary,
    "--secondary-foreground": tokens.colors.secondaryForeground,
    "--destructive": tokens.colors.destructive,
    "--destructive-foreground": tokens.colors.destructiveForeground,
    "--border": tokens.colors.border,
    "--input": tokens.colors.input,
    "--ring": tokens.colors.ring,
    "--card": tokens.colors.card,
    "--card-foreground": tokens.colors.cardForeground,
    "--radius": "0.5rem",
  }

  return entries
}

# ValueVerse Design System

The ValueVerse design system provides a cohesive collection of foundations, components, and usage guidelines that ensure every surface in the product feels consistent and intentional.

## Foundations

- **Design tokens** are defined in [`tokens.ts`](./tokens.ts) and surfaced globally through the [`DesignSystemProvider`](./DesignSystemProvider.tsx). Tokens cover color, typography, elevation, and radius primitives and are exposed as CSS custom properties so both CSS and Tailwind utilities can consume them.
- **Typography scale** keeps headings and body content aligned. Tokens ship with Tailwind utility recipes that can be composed with semantic markup (e.g. `className={tokens.typography.headings.h2}`) when needed.
- **Accessibility** is a first-class requirement. Components inherit semantic roles, manage focus visibility, and provide keyboard support out of the box by wrapping the Radix UI primitives.

## Components

All UI building blocks live in `frontend/components/ui` and are exported individually. Each component is crafted on top of Radix primitives and Tailwind utilities so styling is predictable and theme-aware. When building a new screen:

1. Import components from `@/components/ui/<component>`.
2. Compose them using the tokens exported from this package.
3. Avoid duplicating styles—if a new variant is required, extend the component instead of recreating it.

## Usage

Wrap your application with the `DesignSystemProvider` (this is done for you in `app/layout.tsx`). If you need to support theming, pass an alternate token set to the provider.

```
<DesignSystemProvider tokens={lightTokens}>
  <App />
</DesignSystemProvider>
```

Refer to the stories in `/components` and the live app pages for concrete usage examples. When adding new components, update this directory with their tokens, anatomy, and guidelines so the library remains the single source of truth.

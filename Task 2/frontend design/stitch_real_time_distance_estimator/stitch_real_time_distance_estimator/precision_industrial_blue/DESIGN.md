---
name: Precision Industrial Blue
colors:
  surface: '#fbf9f9'
  surface-dim: '#dbdada'
  surface-bright: '#fbf9f9'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f5f3f3'
  surface-container: '#efeded'
  surface-container-high: '#e9e8e8'
  surface-container-highest: '#e4e2e2'
  on-surface: '#1b1c1c'
  on-surface-variant: '#43474e'
  inverse-surface: '#303031'
  inverse-on-surface: '#f2f0f0'
  outline: '#74777f'
  outline-variant: '#c4c6cf'
  surface-tint: '#476083'
  primary: '#001833'
  on-primary: '#ffffff'
  primary-container: '#112d4e'
  on-primary-container: '#7c95bc'
  inverse-primary: '#afc8f1'
  secondary: '#2a609c'
  on-secondary: '#ffffff'
  secondary-container: '#8bbbfd'
  on-secondary-container: '#064a85'
  tertiary: '#111922'
  on-tertiary: '#ffffff'
  tertiary-container: '#262d37'
  on-tertiary-container: '#8d94a0'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#d4e3ff'
  primary-fixed-dim: '#afc8f1'
  on-primary-fixed: '#001c3a'
  on-primary-fixed-variant: '#2f486a'
  secondary-fixed: '#d3e3ff'
  secondary-fixed-dim: '#a3c9ff'
  on-secondary-fixed: '#001c39'
  on-secondary-fixed-variant: '#004882'
  tertiary-fixed: '#dce3f0'
  tertiary-fixed-dim: '#c0c7d3'
  on-tertiary-fixed: '#151c25'
  on-tertiary-fixed-variant: '#404752'
  background: '#fbf9f9'
  on-background: '#1b1c1c'
  surface-variant: '#e4e2e2'
typography:
  headline-lg:
    fontFamily: IBM Plex Sans
    fontSize: 32px
    fontWeight: '600'
    lineHeight: 40px
    letterSpacing: -0.02em
  headline-md:
    fontFamily: IBM Plex Sans
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
    letterSpacing: -0.01em
  body-lg:
    fontFamily: IBM Plex Sans
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 28px
  body-md:
    fontFamily: IBM Plex Sans
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  label-md:
    fontFamily: JetBrains Mono
    fontSize: 14px
    fontWeight: '500'
    lineHeight: 20px
    letterSpacing: 0.02em
  label-sm:
    fontFamily: JetBrains Mono
    fontSize: 12px
    fontWeight: '500'
    lineHeight: 16px
    letterSpacing: 0.05em
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  unit: 4px
  gutter: 16px
  margin-mobile: 16px
  margin-desktop: 32px
  container-max-width: 1440px
---

## Brand & Style

This design system centers on a high-precision, industrial aesthetic that prioritizes clarity, technical reliability, and authoritative data visualization. Moving away from warmer tones, this version adopts a clinical and professional palette of cool blues and grays, evoking the feeling of high-end engineering software and advanced vision systems.

The style is **Corporate / Modern** with a lean towards **Technical Minimalism**. It utilizes a structured, high-contrast interface to ensure that critical industrial data is legible in varied lighting conditions. The emotional response is one of stability, expertise, and cold-room precision.

## Colors

The palette is strictly cool-toned to maintain an analytical atmosphere. 

- **Primary (#112D4E):** Used for primary navigation, headings, and high-priority action buttons. This deep blue provides the "anchor" for the UI.
- **Secondary (#3F72AF):** Applied to active states, icons, and interactive elements that require distinction from the primary hierarchy.
- **Surface (#DBE2EF):** A soft, blue-gray used for container backgrounds, input fields, and borders. It provides enough contrast against the background to define spatial boundaries.
- **Background (#F9F7F7):** A crisp, off-white background that reduces eye strain compared to pure white while maintaining high contrast for text.

## Typography

The typography system is split between **IBM Plex Sans** for its corporate, systematic reliability and **JetBrains Mono** for technical data.

- **IBM Plex Sans** is used for all interface copy, ensuring a professional and human-readable experience.
- **JetBrains Mono** is reserved for labels, status indicators, and numerical data, reinforcing the "vision system" and industrial feel. 
- Headlines use the Deep Blue (#112D4E) to establish clear hierarchy, while body text uses a slightly softened version for long-form readability.

## Layout & Spacing

This design system uses a **Fixed Grid** model on desktop to maintain alignment across dense data dashboards, and a **Fluid Grid** on mobile for accessibility.

- **Grid:** 12-column layout for desktop (1440px max-width) and a 4-column layout for mobile devices.
- **Rhythm:** A strict 4px base unit informs all padding and margins (4, 8, 12, 16, 24, 32, 48, 64).
- **Density:** Elements are spaced with moderate density. Information density should be high in the center of the UI (using the 4px grid) while outer margins remain generous to focus the user’s attention.

## Elevation & Depth

To maintain the industrial aesthetic, this design system avoids soft, floating shadows. Instead, it utilizes **Tonal Layers** and **Low-contrast Outlines**.

- **Layers:** Depth is created by placing #F9F7F7 cards on #DBE2EF surfaces, or vice versa.
- **Borders:** 1px solid strokes in #DBE2EF are preferred over shadows to define boundaries.
- **Active State:** When an element is raised, it uses a very subtle, tight shadow (Blur: 4px, Color: rgba(17, 45, 78, 0.1)) to simulate a slight physical lift from the dashboard.

## Shapes

The shape language is "Soft" (Level 1). While a technical system often leans toward sharp corners, a slight 4px (0.25rem) radius is applied to buttons, input fields, and containers to make the interface feel modern and high-end rather than dated.

- **Base Radius:** 4px for standard components.
- **Large Radius:** 8px for major dashboard cards.
- **Interactive Elements:** Buttons maintain a consistent 4px radius to feel like physical keycaps.

## Components

- **Buttons:** Primary buttons are solid Deep Blue (#112D4E) with white text. Secondary buttons are outlined in Medium Blue (#3F72AF).
- **Chips:** Used for status. "Active" chips use Medium Blue backgrounds with white mono-spaced text. "Idle" chips use Light Blue/Gray (#DBE2EF) backgrounds.
- **Input Fields:** Backgrounds are #F9F7F7 with 1px #DBE2EF borders. On focus, the border shifts to Medium Blue (#3F72AF).
- **Cards:** Dashboard cards use a #F9F7F7 background with a 1px #DBE2EF border. Header sections within cards can be tinted with #DBE2EF to separate meta-data from content.
- **Data Lists:** Use alternating row colors (Zebra striping) using #F9F7F7 and a 2% tint of #DBE2EF for high-density legibility.
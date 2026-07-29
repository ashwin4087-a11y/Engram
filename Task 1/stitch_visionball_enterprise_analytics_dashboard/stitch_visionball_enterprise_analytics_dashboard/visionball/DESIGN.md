---
name: VisionBall
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
  on-surface-variant: '#424750'
  inverse-surface: '#303031'
  inverse-on-surface: '#f2f0f0'
  outline: '#727781'
  outline-variant: '#c2c6d1'
  surface-tint: '#2a609c'
  primary: '#215995'
  on-primary: '#ffffff'
  primary-container: '#3f72af'
  on-primary-container: '#f2f5ff'
  inverse-primary: '#a3c9ff'
  secondary: '#585f6a'
  on-secondary: '#ffffff'
  secondary-container: '#d9e0ed'
  on-secondary-container: '#5c636e'
  tertiary: '#40597c'
  on-tertiary: '#ffffff'
  tertiary-container: '#587196'
  on-tertiary-container: '#f2f5ff'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#d3e3ff'
  primary-fixed-dim: '#a3c9ff'
  on-primary-fixed: '#001c39'
  on-primary-fixed-variant: '#004882'
  secondary-fixed: '#dce3f0'
  secondary-fixed-dim: '#c0c7d3'
  on-secondary-fixed: '#151c25'
  on-secondary-fixed-variant: '#404752'
  tertiary-fixed: '#d4e3ff'
  tertiary-fixed-dim: '#afc8f1'
  on-tertiary-fixed: '#001c3a'
  on-tertiary-fixed-variant: '#2f486a'
  background: '#fbf9f9'
  on-background: '#1b1c1c'
  surface-variant: '#e4e2e2'
typography:
  headline-xl:
    fontFamily: Inter
    fontSize: 48px
    fontWeight: '700'
    lineHeight: 56px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Inter
    fontSize: 32px
    fontWeight: '700'
    lineHeight: 40px
    letterSpacing: -0.01em
  headline-lg-mobile:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '700'
    lineHeight: 32px
  headline-md:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  body-lg:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 28px
  body-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-sm:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  label-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '600'
    lineHeight: 16px
    letterSpacing: 0.01em
  label-sm:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '600'
    lineHeight: 16px
    letterSpacing: 0.05em
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  unit: 4px
  gutter: 24px
  margin-desktop: 64px
  margin-tablet: 32px
  margin-mobile: 16px
  container-max: 1280px
---

## Brand & Style

This design system is built for a high-trust, data-driven environment that balances enterprise reliability with a modern, fluid user experience. The aesthetic leans into **Corporate Minimalism**, prioritizing clarity, structural integrity, and professional poise. 

The personality is authoritative yet accessible, moving away from organic greens toward a more technical and dependable blue-based spectrum. The interface should feel spacious and intentional, evoking a sense of calm efficiency and precision. By utilizing generous whitespace and a disciplined color application, the UI directs focus toward critical data and decision-making workflows.

## Colors

The color palette is engineered for professional environments where legibility and visual hierarchy are paramount. 

- **Primary Accent (#3F72AF):** A medium blue used for primary actions, active states, and highlighting key information. It serves as the functional anchor of the UI.
- **Deep Contrast (#112D4E):** A dark navy reserved for primary text, headings, and high-impact UI elements. It provides the necessary weight to ground the design.
- **Secondary/Container (#DBE2EF):** A pale blue used for structural elements, secondary buttons, subtle borders, and background containers to differentiate content zones without adding visual noise.
- **Surface/Background (#F9F7F7):** An off-white/light gray that serves as the base canvas, reducing eye strain compared to pure white while maintaining a clean, professional look.

## Typography

This design system utilizes **Inter** exclusively to leverage its systematic, utilitarian nature. The typeface's tall x-height and neutral personality ensure high legibility in data-dense SaaS environments.

- **Headlines:** Use Bold (700) or SemiBold (600) weights in Dark Navy (#112D4E) to establish clear hierarchy.
- **Body Text:** Use Regular (400) weight for long-form content. For secondary information, use a slight opacity reduction or the Medium Blue (#3F72AF) sparingly.
- **Labels:** Use SemiBold (600) for UI controls, navigation items, and button text to differentiate functional elements from static content.

## Layout & Spacing

The layout follows a **Fluid Grid** model with a maximum container width for desktop readability. 

- **Grid:** A 12-column grid is used for desktop and tablet, collapsing to 4 columns for mobile. 
- **Rhythm:** An 8px base unit (derived from the 4px micro-unit) governs all padding and margin decisions to ensure mathematical harmony.
- **Adaptive Rules:** On mobile, margins reduce to 16px and vertical stack spacing increases to maintain "tappable" hit areas and prevent visual crowding.

## Elevation & Depth

Hierarchy is established through **Tonal Layers** rather than heavy shadows, aligning with the minimal enterprise aesthetic.

- **Level 0 (Surface):** The base background (#F9F7F7).
- **Level 1 (Containers):** Cards and content areas use the Pale Blue (#DBE2EF) or pure white with a subtle 1px border in #DBE2EF to create separation.
- **Shadows:** When necessary for overlays (modals/dropdowns), use "Ambient Shadows"—extremely soft, low-opacity (#112D4E at 8% alpha) with a large blur radius and no spread, creating a natural lifted effect.

## Shapes

The shape language is consistently **Rounded**, striking a balance between the rigidness of sharp corners and the playfulness of pill shapes.

- **Standard Elements:** Buttons, input fields, and small cards use a 0.5rem (8px) radius.
- **Large Containers:** Main content sections and modals use a 1rem (16px) radius to soften the larger visual footprint.
- **Interactive States:** Keep corner radii consistent across states to maintain a stable UI footprint.

## Components

- **Buttons:** 
  - *Primary:* Filled with #3F72AF, text in white. 
  - *Secondary:* Filled with #DBE2EF, text in #112D4E.
  - *Ghost:* No fill, border in #DBE2EF, text in #3F72AF.
- **Input Fields:** Use a white background with a 1px border of #DBE2EF. On focus, the border transitions to #3F72AF with a subtle glow.
- **Cards:** Use a white background with an 8px corner radius and a 1px border of #DBE2EF. Avoid heavy shadows; rely on the border for definition.
- **Chips/Badges:** Small, 4px rounded elements using #DBE2EF background with #112D4E text for a neutral, categorized look.
- **Lists:** Clean rows separated by 1px #DBE2EF horizontal lines. Active items should use a subtle #DBE2EF background tint or a 4px left-border accent in #3F72AF.
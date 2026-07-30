---
name: Industrial Vision System
colors:
  surface: '#fdf8f6'
  surface-dim: '#ddd9d7'
  surface-bright: '#fdf8f6'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f7f3f0'
  surface-container: '#f2edeb'
  surface-container-high: '#ece7e5'
  surface-container-highest: '#e6e2df'
  on-surface: '#1c1b1a'
  on-surface-variant: '#4d463d'
  inverse-surface: '#31302f'
  inverse-on-surface: '#f4f0ee'
  outline: '#7e766c'
  outline-variant: '#d0c5ba'
  surface-tint: '#6b5c47'
  primary: '#6b5c47'
  on-primary: '#ffffff'
  primary-container: '#c9b59c'
  on-primary-container: '#554633'
  inverse-primary: '#d8c3aa'
  secondary: '#645d57'
  on-secondary: '#ffffff'
  secondary-container: '#ebe1d8'
  on-secondary-container: '#6a635d'
  tertiary: '#615e59'
  on-tertiary: '#ffffff'
  tertiary-container: '#bcb7b2'
  on-tertiary-container: '#4b4844'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#f5dfc5'
  primary-fixed-dim: '#d8c3aa'
  on-primary-fixed: '#241a09'
  on-primary-fixed-variant: '#534431'
  secondary-fixed: '#ebe1d8'
  secondary-fixed-dim: '#cec5bd'
  on-secondary-fixed: '#1f1b16'
  on-secondary-fixed-variant: '#4c4640'
  tertiary-fixed: '#e7e1dc'
  tertiary-fixed-dim: '#cbc6c0'
  on-tertiary-fixed: '#1d1b18'
  on-tertiary-fixed-variant: '#494642'
  background: '#fdf8f6'
  on-background: '#1c1b1a'
  surface-variant: '#e6e2df'
typography:
  headline-xl:
    fontFamily: Inter
    fontSize: 40px
    fontWeight: '700'
    lineHeight: 48px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Inter
    fontSize: 32px
    fontWeight: '600'
    lineHeight: 40px
    letterSpacing: -0.01em
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
  code-md:
    fontFamily: JetBrains Mono
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 22px
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  base: 8px
  xs: 4px
  sm: 12px
  md: 16px
  lg: 24px
  xl: 32px
  gutter: 24px
  margin: 32px
---

## Brand & Style

This design system is engineered for high-stakes computer vision and industrial automation environments. The visual narrative combines the rugged reliability of earth-toned industrial hardware with the clinical precision of modern software engineering. It evokes a "Mission Control" atmosphere—authoritative, utilitarian, and calm under pressure.

The aesthetic follows a **Modern Corporate** style infused with **Technical Functionalism**. It prioritizes information density and analytical clarity through a disciplined card-based layout. By blending organic, desaturated earth tones with a strict geometric grid, the UI feels like a high-end physical console. Surfaces are flat or subtly layered, avoiding unnecessary decorative effects to ensure the user's focus remains entirely on the data and visual streams.

## Colors

The palette is derived from industrial raw materials: sand, stone, and iron.

- **Primary (#C9B59C):** A tactical tan used for primary actions, active states, and key highlights. It provides enough warmth to stand out against the cooler grey tones without causing visual fatigue.
- **Secondary (#D9CFC7):** A neutral stone grey for secondary UI elements, non-active states, and subtle grouping.
- **Tertiary (#EFE9E3):** The foundational surface color. This off-white reduces glare compared to pure white, enhancing long-term readability in professional monitoring contexts.
- **Neutral (#1A1918):** A deep charcoal used for high-contrast text, inverted buttons, and heavy borders. It anchors the light palette with a sense of weight and authority.

Functional colors (Success/Error) should be desaturated to match the industrial aesthetic, using deep forest greens and oxblood reds rather than neon variants.

## Typography

The typography strategy separates **human-centric communication** from **machine-centric data**.

- **Inter** is utilized for the core interface hierarchy. It provides exceptional legibility for headings and prose, maintaining a professional and neutral tone.
- **JetBrains Mono** is reserved for the "analytical layer." All metrics, timestamps, coordinate data, and code snippets must use this monospaced typeface to emphasize precision and allow for easy character differentiation in dense data views.

On mobile devices, scale `headline-xl` down to `headline-lg` and maintain `body-md` as the minimum comfortable reading size.

## Layout & Spacing

The layout employs a **12-column fluid grid** for desktop and tablet, transitioning to a single-column stack on mobile. 

- **Grid System:** Use a 24px gutter to maintain a clean separation between data-heavy cards. 
- **Card-Based Architecture:** All content is encapsulated within cards to create clear visual boundaries. 
- **Rhythm:** Spacing follows a strict 8px baseline. Use 16px (`md`) for internal card padding and 24px (`lg`) for section headers to create a breathable yet dense environment.
- **Safe Zones:** Content should maintain a 32px outer margin from the edge of the viewport on desktop, reducing to 16px on mobile.

## Elevation & Depth

Hierarchy is established through **Tonal Layers** and **Low-Contrast Outlines** rather than aggressive shadows. 

- **Surfaces:** Use `#EFE9E3` as the base canvas. Secondary surfaces (like sidebar or header) use `#D9CFC7`.
- **Borders:** Cards and input fields utilize a 1px solid border in a slightly darker shade than their background (e.g., `#BCB0A5`) to define shape.
- **Shadows:** Avoid shadows on standard elements. Use a single, highly diffused "Ambient Shadow" (10% opacity of `#1A1918` with 20px blur) exclusively for temporary overlays like modals or dropdown menus to lift them off the "console" surface.

## Shapes

The design system uses a **Rounded** shape language to soften the industrial palette, making the high-tech tool feel more approachable.

- **Primary Radius:** 16px (`1rem`) for all main content cards and containers.
- **Component Radius:** 8px (`0.5rem`) for buttons, input fields, and tags.
- **Circular:** Reserved exclusively for user avatars and status indicators (e.g., live recording dots).

## Components

- **Buttons:**
    - **Primary:** Solid `#C9B59C` background with `#1A1918` text. High visibility for main actions.
    - **Secondary:** Solid `#D9CFC7` background with `#1A1918` text.
    - **Inverted:** Solid `#1A1918` background with `#EFE9E3` text. Used for global navigation or critical controls.
    - **Outlined:** Transparent background with `#1A1918` border and text.

- **Input Fields:** Use `#D9CFC7` for the background with a 1px border. Focus states should switch the border to `#C9B59C`. Labels must use `label-sm` (JetBrains Mono) placed above the field.

- **Chips/Tags:** Small 8px rounded elements using `#D9CFC7` for metadata. Technical tags (e.g., "CPU: 42%") must use JetBrains Mono.

- **Cards:** White or Tertiary background, 16px corner radius, 1px subtle border. No shadow unless hovering.

- **Data Tables:** Row-based layout with `#1A1918` text for headers (Inter, Bold) and `#1A1918` for data (JetBrains Mono). Use subtle horizontal separators in `#D9CFC7`.

- **Icons:** Outlined, 2px stroke weight, consistently using `#1A1918`.
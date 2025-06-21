# VALUE INVESTING DASHBOARD - DESIGN SPECIFICATIONS

## 1. VISUAL DESIGN LANGUAGE

**Consistency with Technical Dashboard:**
- Maintain identical card structure and spacing
- Use same color palette for signal strength (Red → Orange → Yellow → Light Green → Dark Green)
- Match typography: Clean sans-serif, hierarchical sizing
- Preserve hover states and transitions

**Key Visual Differences:**
- Primary accent: Deep Blue (#2563EB) instead of technical's purple
- Icons: Finance/business themed vs technical indicators
- Score gauge: Dollar sign center vs percentage

## 2. COMPONENT SPECIFICATIONS

### Header Section
```
[Company Logo] [Company Name]                    [$XXX.XX]
[Sector] • [Industry] • [Market Cap]             [+X.XX(+X.XX%)]

[Fundamental Score Toggle: Conservative | GARP | Deep Value]
```

### Fundamental Score Widget (Right Side)
- Circular gauge (0-100) with dollar sign center
- Color coding based on score ranges
- "Investment Thesis" expandable section below
- Investor profile selector integrated

### Primary Cards Layout

**Card Structure Template:**
```
┌─────────────────────────────────┐
│ [Icon] CARD TITLE          [🟡]  │
│ ●●●●○ Signal Strength            │
│ ─────────────────────────────── │
│ HEADLINE STATUS                  │
│ Supporting metrics with values   │
│ "Quick insight for action"       │
│ [Detailed] [Export]              │
└─────────────────────────────────┘
```

### Color System
- **Background**: White with subtle gray borders (#E5E7EB)
- **Signal Colors**: 
  - 5: #059669 (Dark Green)
  - 4: #34D399 (Light Green) 
  - 3: #FCD34D (Yellow)
  - 2: #FB923C (Orange)
  - 1: #EF4444 (Red)
- **Text**: #111827 (primary), #6B7280 (secondary)
- **Interactive**: #2563EB (links), #DBEAFE (hover)

## 3. RESPONSIVE BEHAVIOR

### Desktop (>1024px)
- 2-column grid for primary cards
- 4-column grid for secondary cards
- Side-by-side score and details

### Tablet (768-1024px)
- 2-column maintained
- Stacked score widget
- Condensed metrics

### Mobile (<768px)
- Single column
- Collapsible cards
- Swipeable investor profiles
- Bottom sheet for details

## 4. INTERACTION PATTERNS

### Card Interactions
- **Hover**: Subtle elevation shadow, 0.2s transition
- **Click "Detailed"**: Slide-down animation revealing:
  - Historical chart (5Y, 3Y, 1Y toggles)
  - Peer comparison table
  - Educational content
  
### Score Interactions
- **Gauge**: Animated fill on load (1s ease-out)
- **Breakdown**: Click "Investment Thesis" for weighted components
- **Profile Switch**: Instant recalculation with fade transition

### Data Loading States
- Skeleton screens matching card layout
- Shimmer effect during updates
- Error states with retry option

## 5. ICONOGRAPHY

### Primary Card Icons
- Valuation Matrix: 💎 (gem)
- Business Quality: 🏆 (trophy)

### Secondary Card Icons
- Profitability: 📈 (chart increasing)
- Financial Health: 🏥 (hospital/cross)
- Growth Momentum: 🚀 (rocket)
- Management: 👔 (business person)

### Status Icons
- Risk Warnings: 🔴🟠🟡 (matching technical)
- Info tooltips: ℹ️ (on hover)
- Trend arrows: ↗️↘️➡️

## 6. TYPOGRAPHY

### Font Stack
```css
font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
```

### Size Hierarchy
- Card Title: 16px/600 weight
- Headline: 18px/700 weight
- Metrics: 14px/400 weight
- Supporting: 12px/400 weight
- Quick Take: 13px/500 weight italic

## 7. ANIMATION SPECIFICATIONS

### Transitions
- Card hover: `transform: translateY(-2px); box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);`
- Score change: `transition: all 0.3s ease-out;`
- Tab switch: `opacity transition 0.2s;`
- Details expand: `max-height transition 0.3s ease-in-out;`

### Loading Animations
- Skeleton pulse: `@keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }`
- Score fill: `stroke-dasharray animation 1s ease-out;`

## 8. ACCESSIBILITY

### Requirements
- WCAG 2.1 AA compliance
- All interactive elements keyboard accessible
- ARIA labels for screen readers
- Color contrast ratios: 4.5:1 minimum
- Focus indicators visible

### Implementation
- Skip links for navigation
- Semantic HTML structure
- Alt text for all icons
- Readable without color alone
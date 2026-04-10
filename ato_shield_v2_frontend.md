# ATO Shield v2 — Frontend Design Document

> Visual and UX specification for all three dashboard screens.
> To be handed to the AI at Phase 3 alongside the master document.
> Last updated: April 2026.

---

## 1. Design Direction

### The Feeling
Professional, clinical, trustworthy. This is a workstation — not a consumer app, not a marketing site. The analyst spends 8 hours a day here. The design must reduce cognitive load, communicate urgency instantly, and never get in the way of a decision.

Think: **Bloomberg Terminal meets modern SaaS** — the information density and seriousness of financial software, with the cleanliness and clarity of a well-designed product like Notion or Linear.

### What We're Taking From the References

**From Reference 1 (Finance Dashboard — Light/Dark):**
- The sidebar navigation pattern — fixed left rail, icon + label, clearly active state
- Card-based content layout — content lives in rounded, soft-shadow cards on a neutral background
- The light/dark theme toggle approach — we go dark by default (fraud ops runs better on dark; less eye strain on long shifts, alert colours pop harder)
- Typography scale — large bold numbers for the things that matter most
- The clean separation between navigation and content areas

**From Reference 2 (Digital Marketing Dashboard):**
- The top bar pattern — analyst name + avatar top right, page title top left
- The left nav dark background with white labels — high contrast, always readable
- Card layout with subtle section labels above data
- The schedule/table section — clean rows, status badges with colour coding
- Sparkline charts inline with list items — compact, informative without taking space
- The overall sense of breathing room — generous padding, nothing cramped

### What We're Not Taking
- Donut charts and subscription metrics — wrong context
- Illustration / avatar characters in the sidebar — too casual for a bank tool
- Pastel or gradient heavy colour — needs to feel serious
- Rounded pill buttons everywhere — decisions (BLOCK / FREEZE) need to feel weighty

---

## 2. Colour Palette

### Base (Dark Theme — Default)

| Role | Name | Hex | Usage |
|------|------|-----|-------|
| Background | Void | `#0F1117` | Page background |
| Surface | Panel | `#1A1D27` | Cards, sidebar |
| Surface Raised | Elevated | `#22263A` | Hover states, input backgrounds |
| Border | Subtle | `#2E3348` | Card borders, dividers |
| Text Primary | White | `#F0F2FF` | Headlines, important values |
| Text Secondary | Muted | `#8B90A7` | Labels, secondary info |
| Text Tertiary | Dim | `#555B77` | Timestamps, metadata |

### Brand

| Role | Name | Hex | Usage |
|------|------|-----|-------|
| Brand Primary | Shield Blue | `#2D6BE4` | Active nav item, primary actions, links |
| Brand Accent | Electric | `#4F8EF7` | Hover on brand elements, chart fills |

### Risk Colours (The Most Important Palette)

These must be immediately readable and emotionally clear. No ambiguity.

| Risk Level | Name | Hex | Background Tint | Usage |
|------------|------|-----|-----------------|-------|
| HIGH | Alert Red | `#E84040` | `#2A1515` | HIGH risk badges, threat indicator, urgent alerts |
| MEDIUM | Caution Amber | `#F0A500` | `#2A2210` | MEDIUM risk badges, elevated warnings |
| LOW | Safe Green | `#27AE60` | `#122A1C` | Cleared cases, safe status, All Clear indicator |
| ANOMALY | Anomaly Blue | `#6B8CFF` | `#141A2E` | ANO fraud type specifically |

### Fraud Type Colours (Consistent with v1)

| Code | Colour | Hex |
|------|--------|-----|
| ATO | Red | `#E84040` |
| VEL | Orange | `#FF6B35` |
| AMT | Amber | `#F0A500` |
| NGT | Purple | `#9B59B6` |
| ANO | Blue | `#6B8CFF` |

---

## 3. Typography

### Font
**Inter** — used throughout. Free, professional, optimised for screens and dashboards. Loaded from Google Fonts.

```css
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
```

### Scale

| Role | Size | Weight | Colour | Usage |
|------|------|--------|--------|-------|
| Page Title | 22px | 700 | `#F0F2FF` | Screen heading (e.g. "Operations Centre") |
| Card Heading | 13px | 600 | `#8B90A7` | Section label above a card (uppercase, tracked) |
| Hero Number | 36px | 700 | `#F0F2FF` | Protected value, alert count |
| Body | 14px | 400 | `#F0F2FF` | General content, case details |
| Label | 12px | 500 | `#8B90A7` | Field labels, metadata |
| Timestamp | 12px | 400 | `#555B77` | Time since flagged, received at |
| Badge | 11px | 600 | varies | Fraud type, risk level — uppercase |

### Rules
- Never use font size below 11px
- Card section labels always uppercase with `letter-spacing: 0.08em`
- Numbers that matter (amounts, counts) always in a heavier weight than surrounding text

---

## 4. Layout System

### Grid
- **Sidebar:** 220px fixed width, always visible
- **Top bar:** 56px fixed height
- **Content area:** fills remaining space, max-width 1400px, centered on wide screens
- **Content padding:** 28px all sides
- **Card gap:** 16px

### Cards
```css
background: #1A1D27;
border: 1px solid #2E3348;
border-radius: 12px;
padding: 20px 24px;
```

No heavy drop shadows — the border does the separation work. Consistent with Reference 1's card language.

### Sidebar
```css
width: 220px;
background: #1A1D27;
border-right: 1px solid #2E3348;
padding: 24px 16px;
```

Nav items follow Reference 2's pattern — icon left, label right, active state fills the row with a brand-tinted background:
```css
/* Active nav item */
background: rgba(45, 107, 228, 0.15);
border-radius: 8px;
color: #4F8EF7;
```

---

## 5. Components

### 5.1 Risk Badge
Pill-shaped, coloured by risk level. Used on case cards in the queue and case header.

```
┌──────────┐
│ 🔴 HIGH  │   background: #2A1515, color: #E84040, border: 1px solid #E84040
└──────────┘

┌────────────┐
│ 🟡 MEDIUM │   background: #2A2210, color: #F0A500, border: 1px solid #F0A500
└────────────┘

┌──────────┐
│ 🟢 LOW   │   background: #122A1C, color: #27AE60, border: 1px solid #27AE60
└──────────┘
```

```css
.badge {
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  padding: 3px 10px;
  border-radius: 20px;
}
```

### 5.2 Fraud Type Tag
Smaller than risk badge. Sits beside the risk badge on case cards.

```
[ ATO ]  [ VEL ]  [ AMT ]  [ NGT ]  [ ANO ]
```

Each uses its fraud type colour at 20% opacity background, full opacity text and border.

### 5.3 Threat Indicator
The centrepiece of Screen 1. Large, immediate, impossible to miss.

```
┌────────────────────────────────┐
│                                │
│   ●  ELEVATED                  │
│   3 cases require attention    │
│                                │
└────────────────────────────────┘
```

| State | Label | Dot Colour | Card Border |
|-------|-------|-----------|-------------|
| All Clear | ALL CLEAR | `#27AE60` | `#27AE60` at 40% |
| Elevated | ELEVATED | `#F0A500` | `#F0A500` at 40% |
| Critical | CRITICAL | `#E84040` | `#E84040` — pulses |

The dot pulses with a CSS animation when state is CRITICAL.

### 5.4 Case Card (Alert Queue Row)
Full width card. Each flagged case is one row.

```
┌──────────────────────────────────────────────────────────────────────────┐
│  🔴 HIGH   [ ATO ]    Priya Sharma          8 min ago          [Review →]│
│            ₹1,20,000  New device · 3am · 4th transfer today              │
└──────────────────────────────────────────────────────────────────────────┘
```

- Left: risk badge + fraud type tag
- Middle left: customer name (bold, 14px) + amount (bold, 16px, white)
- Middle right: one-line reason summary (14px, muted)
- Right: timestamp (dim) + Review button
- On hover: card background lifts to `#22263A`, cursor pointer
- HIGH cases have a left border accent: `border-left: 3px solid #E84040`
- MEDIUM cases: `border-left: 3px solid #F0A500`

### 5.5 Decision Buttons
The most important UI element. Four actions, visually weighted by consequence.

```
[ BLOCK ]  [ FREEZE ACCOUNT ]  [ ESCALATE ]  [ CLEAR ]
```

| Action | Style | Colour |
|--------|-------|--------|
| BLOCK | Filled, bold | `#E84040` background — most destructive action, most prominent |
| FREEZE | Filled, bold | `#F0A500` background |
| ESCALATE | Outlined | `#2D6BE4` border + text |
| CLEAR | Ghost | `#8B90A7` text only — least destructive, least prominent |

```css
.btn-block {
  background: #E84040;
  color: #fff;
  font-weight: 700;
  font-size: 14px;
  padding: 12px 24px;
  border-radius: 8px;
  border: none;
  cursor: pointer;
}

.btn-clear {
  background: transparent;
  color: #8B90A7;
  font-weight: 500;
  font-size: 14px;
  padding: 12px 24px;
  border-radius: 8px;
  border: 1px solid #2E3348;
  cursor: pointer;
}
```

Buttons on hover darken by 10%. No flat colour buttons — all have slight depth.

### 5.6 Stat Card (Operations Centre)
Small card showing one number with context.

```
┌──────────────────────────┐
│  SCREENED TODAY           │
│  4,231                   │
│  transactions             │
└──────────────────────────┘
```

Card label: 12px, uppercase, muted.
Hero number: 36px, bold, white.
Sub-label: 13px, muted.

### 5.7 Protected Value Card
The headline number on Screen 1. Larger than other stat cards.

```
┌──────────────────────────────┐
│  PROTECTED TODAY             │
│  ₹ 42,31,500                 │
│  across 4,231 transactions   │
└──────────────────────────────┘
```

Hero number: 42px, bold, `#27AE60` (green — money saved = good).

---

## 6. Screen-by-Screen Layouts

### Screen 1 — Operations Centre

```
┌─────────┬──────────────────────────────────────────────────────────┐
│         │  Operations Centre                    Priya [analyst] ▼  │
│  LOGO   ├──────────────────────────────────────────────────────────┤
│         │                                                          │
│  ──── ─ │  ┌──────────────┐  ┌──────┐  ┌──────┐  ┌────────────┐  │
│  Home ● │  │ THREAT LEVEL │  │CASES │  │ SCR- │  │ PROTECTED  │  │
│  Queue  │  │              │  │OPEN  │  │ EENED│  │ TODAY      │  │
│  Cases  │  │ ● ELEVATED   │  │  3   │  │ 4,231│  │ ₹42,31,500 │  │
│         │  │ 3 need attn  │  │      │  │      │  │            │  │
│  ─────  │  └──────────────┘  └──────┘  └──────┘  └────────────┘  │
│  Logout │                                                          │
│         │  ┌────────────────────────────────────────────────────┐  │
│         │  │  TRANSACTION VOLUME — TODAY                        │  │
│         │  │                                                    │  │
│         │  │  [bar chart — hourly volume, flagged in red/amber] │  │
│         │  │                                                    │  │
│         │  └────────────────────────────────────────────────────┘  │
│         │                                                          │
│         │  ┌─────────────────────────┐  ┌──────────────────────┐  │
│         │  │  RECENT FLAGS           │  │  TODAY'S BREAKDOWN   │  │
│         │  │  [last 3 cases, compact]│  │  [donut: ATO/VEL/AMT]│  │
│         │  └─────────────────────────┘  └──────────────────────┘  │
└─────────┴──────────────────────────────────────────────────────────┘
```

**Layout notes:**
- 4-column stat card row at top — equal width cards
- Full-width transaction volume chart below (bar chart, Plotly, dark themed)
- Two-column row at bottom — recent flags list left, fraud type breakdown donut right
- Threat level card has coloured left border matching its state

---

### Screen 2 — Alert Queue

```
┌─────────┬──────────────────────────────────────────────────────────┐
│         │  Alert Queue                    3 open    Priya [▼]      │
│  LOGO   ├──────────────────────────────────────────────────────────┤
│         │                                                          │
│  Home   │  [ All  |  HIGH  |  MEDIUM ]          [ Oldest | Newest ]│
│  Queue● │                                                          │
│  Cases  │  ┌──────────────────────────────────────────────────┐   │
│         │  │ 🔴 HIGH [ATO]  Priya Sharma        8 min ago  →  │   │
│  ─────  │  │ ₹1,20,000   New device · 3am · 4th transfer     │   │
│  Logout │  └──────────────────────────────────────────────────┘   │
│         │  ┌──────────────────────────────────────────────────┐   │
│         │  │ 🔴 HIGH [VEL]  Rahul Verma        14 min ago  →  │   │
│         │  │ ₹8,400     5 transfers in 12 minutes             │   │
│         │  └──────────────────────────────────────────────────┘   │
│         │  ┌──────────────────────────────────────────────────┐   │
│         │  │ 🟡 MED [NGT]   Sunita Patel       31 min ago  →  │   │
│         │  │ ₹62,000    Late night, new location              │   │
│         │  └──────────────────────────────────────────────────┘   │
│         │                                                          │
│         │  — No more open cases —                                  │
└─────────┴──────────────────────────────────────────────────────────┘
```

**Layout notes:**
- Filter tabs: All / HIGH / MEDIUM — tab style, active tab underlined in brand blue
- Sort toggle top right — simple, not prominent
- Each case is a full-width card with left border colour
- When queue is empty: centered empty state — "✓ All clear. No open cases." in green
- New case arrives via WebSocket — slides in at the top with a subtle flash animation

---

### Screen 3 — Case Investigation

```
┌─────────┬──────────────────────────────────────────────────────────┐
│         │  ← Back to Queue          Case #4821       Priya [▼]    │
│  LOGO   ├──────────────────────────────────────────────────────────┤
│         │                                                          │
│  Home   │  ┌──────────────────────────────────────────────────┐   │
│  Queue  │  │ 🔴 HIGH RISK — Account Takeover (ATO)            │   │
│  Cases● │  │ Flagged 8 minutes ago · Transaction TXN_9821ABC  │   │
│         │  └──────────────────────────────────────────────────┘   │
│  ─────  │                                                          │
│  Logout │  ┌───────────────────────┐  ┌──────────────────────┐   │
│         │  │ TRANSACTION           │  │ CUSTOMER PROFILE      │   │
│         │  │ Amount  ₹1,20,000     │  │ Priya Sharma          │   │
│         │  │ To      HDFC ****4821 │  │ Account since  2019   │   │
│         │  │ Via     UPI           │  │ Avg amount    ₹8,200  │   │
│         │  │ Time    3:14 AM       │  │ City          Mumbai  │   │
│         │  │ Device  ⚠ New device  │  │ Last login  3:11 AM  │   │
│         │  └───────────────────────┘  └──────────────────────┘   │
│         │                                                          │
│         │  ┌──────────────────────────────────────────────────┐   │
│         │  │ WHY THIS WAS FLAGGED                             │   │
│         │  │ ⚠ Transfer is 14× larger than customer average   │   │
│         │  │ ⚠ Device has never been used on this account     │   │
│         │  │ ⚠ Transaction at 3:14 AM — outside all activity  │   │
│         │  │ ⚠ 4th transaction in 90 minutes                  │   │
│         │  └──────────────────────────────────────────────────┘   │
│         │                                                          │
│         │  ┌──────────────────────────────────────────────────┐   │
│         │  │ RECENT ACTIVITY                                  │   │
│         │  │ ₹7,200  · yesterday    · Mumbai  · usual device  │   │
│         │  │ ₹12,000 · 3 days ago   · Mumbai  · usual device  │   │
│         │  │ ₹3,400  · 5 days ago   · Mumbai  · usual device  │   │
│         │  └──────────────────────────────────────────────────┘   │
│         │                                                          │
│         │  ┌──────────────────────────────────────────────────┐   │
│         │  │ YOUR DECISION                                    │   │
│         │  │ [BLOCK] [FREEZE ACCOUNT] [ESCALATE] [CLEAR]     │   │
│         │  └──────────────────────────────────────────────────┘   │
└─────────┴──────────────────────────────────────────────────────────┘
```

**Layout notes:**
- Alert header spans full width — coloured background matching risk level (`#2A1515` for HIGH)
- Transaction + Customer Profile in two equal columns
- "WHY THIS WAS FLAGGED" section has amber left border — draws the eye immediately
- Each reason bullet prefixed with ⚠ icon in amber
- Recent Activity is a compact table — no heavy borders, just subtle row separators
- Decision panel pinned to bottom of content, always visible without scrolling if possible
- After decision: brief confirmation toast ("Case blocked. Loading next case...") then auto-advance

---

## 7. Navigation

### Sidebar Items

```
┌─────────────┐
│  🛡 ATO Shield│  ← Logo + product name
├─────────────┤
│  ⊞ Overview  │  → Operations Centre (Screen 1)
│  ⚑ Queue   3│  → Alert Queue (Screen 2) — badge shows open count
│  ◉ Cases    │  → Recent resolved cases
├─────────────┤
│  ⚙ Settings │
│  → Sign Out  │
└─────────────┘
```

- Queue nav item has a live badge showing open case count — updates via WebSocket
- Active item: brand blue tinted background row
- Sidebar never collapses in v2 — always expanded (220px)
- Bottom section (Settings, Sign Out) pinned to bottom of sidebar

### Top Bar

```
[Page Title]                              [Analyst Name ▼]
```

- Left: current screen name
- Right: analyst name with dropdown (Sign Out only for now)
- No search bar in v2 — not needed yet
- No notification bell — WebSocket handles alerts inline

---

## 8. Micro-interactions and States

### Loading
- Skeleton screens — grey shimmer blocks where content will load
- Never a full-page spinner
- Cards load independently — content appears as it's ready

### WebSocket — New Case Arrives
1. Queue badge in sidebar increments with a brief pulse
2. If on Alert Queue screen: new case card slides in from top, flashes amber once
3. If on another screen: toast notification appears bottom-right — "⚠ New HIGH risk case — Priya Sharma" with a [Review] link

### Decision Confirmation
1. Analyst clicks BLOCK
2. Button shows spinner for 300ms (API call)
3. Brief green toast: "✓ Case blocked successfully"
4. 800ms pause then auto-advance to next open case
5. If no more cases: redirect to queue with "✓ All clear" state

### Empty States
- Alert Queue empty: centered icon + "✓ No open cases. Queue is clear." in green text
- No cases at all: "🛡 System active. Screening transactions." in muted text

### Error States
- API error on decision: red toast "Decision failed — please try again" — case stays open
- WebSocket disconnect: subtle banner "⚠ Live updates paused — reconnecting..." disappears when reconnected

---

## 9. CSS Variables (Full Reference)

```css
:root {
  /* Backgrounds */
  --bg-void: #0F1117;
  --bg-panel: #1A1D27;
  --bg-elevated: #22263A;

  /* Borders */
  --border-subtle: #2E3348;

  /* Text */
  --text-primary: #F0F2FF;
  --text-secondary: #8B90A7;
  --text-dim: #555B77;

  /* Brand */
  --brand: #2D6BE4;
  --brand-light: #4F8EF7;

  /* Risk */
  --risk-high: #E84040;
  --risk-high-bg: #2A1515;
  --risk-medium: #F0A500;
  --risk-medium-bg: #2A2210;
  --risk-low: #27AE60;
  --risk-low-bg: #122A1C;

  /* Fraud types */
  --fraud-ato: #E84040;
  --fraud-vel: #FF6B35;
  --fraud-amt: #F0A500;
  --fraud-ngt: #9B59B6;
  --fraud-ano: #6B8CFF;

  /* Spacing */
  --sidebar-width: 220px;
  --topbar-height: 56px;
  --content-padding: 28px;
  --card-gap: 16px;
  --card-radius: 12px;
  --card-padding: 20px 24px;

  /* Typography */
  --font: 'Inter', sans-serif;
}
```

---

## 10. What to Hand the AI at Phase 3

When building the dashboard templates, upload:

1. `ato_shield_v2_master.md` — full product context
2. This file (`ato_shield_v2_frontend.md`) — design spec
3. The specific screen wireframe from Section 6 for the screen being built
4. A real case JSON from the database — so AI populates with real values, not placeholders
5. `base.html` when building any screen after Screen 1

---

## 11. What's Deliberately Not in v2 Frontend

- ❌ Light mode toggle — dark only in v2
- ❌ Mobile responsive layout — this is a desktop workstation tool
- ❌ Data export buttons — not needed in v2 scope
- ❌ Any chart showing ML model performance — invisible to analysts
- ❌ Notification bell icon — WebSocket handles this inline
- ❌ User management UI — handled manually / admin config in v2
- ❌ Any mention of XGBoost, SHAP, Isolation Forest, risk scores as numbers

---

*Frontend design is locked. Next step: agree on any final tweaks, then Phase 3 build begins.*

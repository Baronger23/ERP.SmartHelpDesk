---
name: smarthelpdesk-design-system
description: Guidelines and best practices for creating and maintaining UI screens, presentations, and components for the Smart Helpdesk & Maintenance project using Stitch and DESIGN.md.
---

# SmartHelpDesk Design System & Agent Skill

This skill enforces UI/UX consistency, Design Token adherence, and presentation guidelines for the **Smart Helpdesk & Maintenance (AIS - Alpha Industrial Services)** platform.

## Design Token Compliance (`DESIGN.md`)

All generated UI code, presentation slides, and frontend components MUST conform to the tokens specified in [DESIGN.md](file:///e:/DUT.K1N4/HTTT/Project_SmartHelpDesk_Mainternance/DESIGN.md):

* **Color Palette (Modern Light Identity)**:
  - Primary Tech Blue: `#1D4ED8` (Cobalt Blue 700 - Key Actions & Highlights)
  - Secondary Slate: `#0F172A` (Deep Slate - High-contrast headings & structure)
  - Tertiary Cyan: `#0284C7` (Sky / Cyan Industrial)
  - Background Neutral: `#F8FAFC` (Slate 50 Alabaster Canvas)
  - Card Surface: `#FFFFFF` (Pure Crisp White)
  - Border / Divider: `#E2E8F0` (Hairline Border Slate 200)
  - Status Indicators: Success (`#047857`), Warning (`#B45309`), Emergency Error (`#DC2626`)
* **Environment Endpoint**:
  - Local Docker Environment: `http://localhost:8080/desk` (Port 8080)
* **Typography**:
  - Headings: `Inter`, weights 600 & 700
  - Body: `Inter`, weights 400 & 500
  - Codes, Timestamps & IDs: `JetBrains Mono` or `monospace`
* **Spacing & Containment**:
  - Spatial rhythm: 8px base grid (8px, 16px, 24px, 32px)
  - Card boundaries: 1px border (`#E2E8F0`) with 12px rounded corners (`rounded-xl`)
  - Elevation: Subtle, crisp borders rather than heavy shadows.

## Verification & Linting

Before finalizing any frontend or presentation deliverables:
```bash
node ./node_modules/@google/design.md/dist/index.js lint DESIGN.md
```
Ensure zero errors and zero contrast ratio warnings.

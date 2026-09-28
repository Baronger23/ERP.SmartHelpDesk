---
version: "alpha"
name: "SmartHelpDesk Modern Light Design System"
description: "Pristine, high-contrast, modern light visual identity and tokens for Alpha Industrial Services (AIS) Smart Helpdesk & Maintenance ERP platform."
colors:
  primary: "#1D4ED8"
  on-primary: "#FFFFFF"
  secondary: "#0F172A"
  on-secondary: "#FFFFFF"
  tertiary: "#0284C7"
  on-tertiary: "#FFFFFF"
  neutral: "#F8FAFC"
  surface: "#FFFFFF"
  on-surface: "#0F172A"
  surface-variant: "#F1F5F9"
  border: "#E2E8F0"
  success: "#047857"
  on-success: "#FFFFFF"
  warning: "#B45309"
  on-warning: "#FFFFFF"
  error: "#DC2626"
  on-error: "#FFFFFF"
typography:
  h1:
    fontFamily: "Inter"
    fontSize: "36px"
    fontWeight: 700
    lineHeight: 1.2
  h2:
    fontFamily: "Inter"
    fontSize: "24px"
    fontWeight: 600
    lineHeight: 1.3
  h3:
    fontFamily: "Inter"
    fontSize: "18px"
    fontWeight: 600
    lineHeight: 1.4
  body-lg:
    fontFamily: "Inter"
    fontSize: "16px"
    fontWeight: 400
    lineHeight: 1.6
  body-md:
    fontFamily: "Inter"
    fontSize: "14px"
    fontWeight: 400
    lineHeight: 1.5
  label-caps:
    fontFamily: "JetBrains Mono"
    fontSize: "12px"
    fontWeight: 600
    lineHeight: 1
    letterSpacing: "0.05em"
rounded:
  sm: "4px"
  md: "8px"
  lg: "12px"
  full: "9999px"
spacing:
  xs: "4px"
  sm: "8px"
  md: "16px"
  lg: "24px"
  xl: "32px"
  2xl: "48px"
components:
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.on-primary}"
    rounded: "{rounded.md}"
    padding: "12px"
  button-primary-hover:
    backgroundColor: "#1E40AF"
    textColor: "{colors.on-primary}"
  card:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.on-surface}"
    rounded: "{rounded.lg}"
    padding: "20px"
  badge-success:
    backgroundColor: "{colors.success}"
    textColor: "{colors.on-success}"
    rounded: "{rounded.sm}"
    padding: "4px"
  badge-warning:
    backgroundColor: "{colors.warning}"
    textColor: "{colors.on-warning}"
    rounded: "{rounded.sm}"
    padding: "4px"
  panel-neutral:
    backgroundColor: "{colors.neutral}"
    textColor: "{colors.on-surface}"
    rounded: "{rounded.md}"
    padding: "16px"
  divider:
    backgroundColor: "{colors.border}"
    height: "1px"
---

## Overview

**Modern Light Enterprise Design System** for **Alpha Industrial Services (AIS)**. 
Built on a foundation of pristine white surfaces, crisp high-contrast typography, and vibrant industrial accents. 
Engineered specifically for clarity, ergonomics, and seamless readability across factory control desks, field service tablets, and executive presentation rooms.

## Colors

The color palette is calibrated for 100% WCAG AA / AAA compliance, eliminating murky dark-on-dark contrast:

- **Primary (`#1D4ED8`):** Tech Cobalt Blue — establishes strong brand presence, primary interactive buttons, and key highlights.
- **Secondary (`#0F172A`):** Deep Industrial Charcoal — used for crisp titles, heavy headers, and authoritative metrics.
- **Tertiary (`#0284C7`):** Cyan Industrial Blue — telemetry indicators, network status, and auxiliary links.
- **Neutral (`#F8FAFC`):** Alabaster Light Canvas — clean, glare-free workspace background.
- **Surface (`#FFFFFF`):** Pure Crisp White — card containers with subtle border boundaries and soft ambient elevation.
- **Surface-Variant (`#F1F5F9`):** Light slate tint for nested data panels, table headers, and pill tags.
- **Border (`#E2E8F0`):** Crisp 1px structural dividing lines.
- **Success (`#047857`):** Verified green for SLA on-time completion, normal telemetry, and resolved tickets.
- **Warning (`#B45309`):** Industrial amber for reorder warnings, buffer thresholds, and SLA clock alerts.
- **Error (`#DC2626`):** Vibrant emergency red for severe machine faults, overdue tickets, and downtime alerts.

## Typography

Typography prioritizes high legibility and information density:

- **Headings (`Inter`):** Bold weights (700, 600) rendered in deep slate (`#0F172A`) for maximum contrast against white and light surfaces.
- **Body Text (`Inter`):** Clean 14px and 16px rendered in slate gray (`#334155`), delivering superior readability without visual fatigue.
- **Code & Metrics (`JetBrains Mono`):** Fixed-width font for ticket identifiers (e.g. `ISSUE-2026-00042`), asset tags (`ACC-ASS-001`), and SLA countdowns.

## Layout & Components

- **Cards & Containers:** Pure white backgrounds (`#FFFFFF`) with 1px border (`#E2E8F0`), 12px border radius, and gentle ambient drop shadows (`0 1px 3px rgba(0, 0, 0, 0.05)`).
- **Pillars & Categories:** Distinctive, soft pastel header backgrounds (`#EFF6FF` for Helpdesk, `#ECFDF5` for Maintenance, `#FFFBEB` for Inventory) paired with dark legible text.
- **Buttons:** Vibrant Cobalt Blue (`#1D4ED8`) with crisp pure white text (`#FFFFFF`), providing immediate affordance.
- **Local Environment Target:** Designed for local development and on-premise execution at `http://localhost:8080/desk`.

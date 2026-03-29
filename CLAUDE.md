# CLAUDE.md — AI Forex Trading Agent

> **This is a completely separate project from Callara.ai.** Do not mix context, code patterns, or architectural decisions between this repo and `/Users/LeJack/Documents/callara.ai`. They share a GitHub org (`callaraai`) but are unrelated products.

---

## Project Overview

An AI-powered Forex trading assistant being built for a collaborator (the trader). Current phase: intake/onboarding UI + building the agent logic. Future goal: autonomous signal detection and potentially self-executing trades.

**Repo:** `github.com/callaraai/trading`
**Local path:** `/Users/LeJack/Documents/trading`
**Stack:** Currently vanilla HTML/CSS/JS (single `index.html`). No framework yet.
**Platform:** TradingView (trader's charting platform). API access not yet set up but trader is willing.

---

## The Trader's Ruleset (Intake — 2026-03-15)

This is the source of truth for the agent's scanner logic. Everything the agent does must trace back to these rules.

### Strategy Overview
EMA crossover + TDI (Traders Dynamic Index) confirmation system on 1H/4H. Rules-based, indicator-driven. Trades during specific session windows.

### Entry Setup (SHORT example — mirror for longs)
1. **1H chart:** 13 EMA crosses **below** 50 EMA
2. **Pullback:** Price pulls back **at least 25 pips** to the 50 EMA
3. **Touch rule:** Price must **touch the 50 EMA at least twice** — no single-wick quick touches
4. **Shift candle:** A candle of **at least 20 pips** forms, closing closer to its low, and the **close must be below the 13 EMA**
5. **TDI (1H):**
   - Yellow market base line must be **below 50**
   - Black RSI line must have **touched at least the 48 level** then crossed **below the red signal line**
   - Black RSI line must be **below 50**
6. **Extra confluence (4H TDI):** Tip of the black RSI line pointing **in the direction of the trade** (down for shorts)

### Invalidation Rules (No-Trade Conditions)
- **No dribble trades** — if price is riding the 50 EMA and shift candle isn't large enough, skip
- **No shark fin** — if TDI RSI line goes outside Bollinger Bands and comes back in (even if all other rules met)
- **No high-impact news** — suppress signals ±30 min of major events
- **Trade window only:** 11 AM Japan time through 9 AM EST, Sunday–Friday (Sunday EST = Monday Japan)

### Setup Grading
**A-grade (ideal):** Clean 13/50 cross → pullback to 50 EMA with 2 clean touches → solid shift candle closing in trade direction, closes on correct side of 13 EMA → TDI below 50 zone, RSI crosses signal line in correct direction, RSI on correct side of 50 → yellow market base line on correct side of 50 → 4H RSI tip pointing in trade direction.

**Alert threshold:** B-grade and above (partial criteria met) — agent alerts even on near-perfect setups.

### Risk Management
| Parameter | Value |
|-----------|-------|
| Max risk per trade | 2% of account |
| Stop loss placement | Below/above market structure |
| Exit method | Dynamic — managed based on price action |
| Breakeven | Yes — at a specific R level (move stop to entry once trade hits 1:1) |
| Daily max loss | Not specified |
| Weekly max loss | 6% (circuit breaker — agent halts signals when hit) |
| Max trades/day | 3 per day, 1 per session |

### Sessions & Pairs
**Active sessions:** London open, London/NY overlap, Asian session

**All pairs:** EUR/USD, GBP/USD, USD/JPY, GBP/JPY, AUD/USD, USD/CAD, USD/CHF, NZD/USD, all majors

**Top priority pairs:** GBP/AUD, EUR/NZD, GBP/USD, GBP/CAD, GBP/NZD, GBP/JPY, USD/JPY

**Critical:** Trader's #1 downfall is **trading correlated pairs simultaneously** — this has caused larger-than-expected daily losses. Agent must detect and flag/prevent entries on correlated pairs when already in a trade.

### Psychology & Discipline
- **Believes in probabilities** — if rules are met, execute even if setup doesn't look perfect
- **News while in trade:** If already in profit when news hits, move stop to breakeven and let news play out
- **Deviation flag:** Agent must flag every time trader deviates from entry criteria
- **Performance metric:** Steadily rising equity curve with minimum drawdown
- **Journaling:** Sporadic (sometimes). Tool: spreadsheet. Wants auto-capture of: entry/exit price & time, chart screenshot, P&L in $ and %

### Fundamentals & Macro
- News-aware strategy — avoids high-impact events
- Uses economic calendar as macro input
- News suppression: ±30 min around major events

### Agent Mode
**Semi-autonomous** — agent alerts and suggests, trader executes (not fully auto yet)

### Alert Preferences
- **Channels:** SMS/text, push notification, Telegram
- **Verbosity:** Full brief (complete analysis, not just signal)
- **In-trade alerts:** Partial profit suggestions
- **Alert on:** B-grade setups and above

---

## Trading Journal App (Session 2 — 2026-03-29)

A dedicated web app for Ben to log and review his trades. Separate from the AI agent work — this is a manual journaling tool first, agent integration later.

### What's Built

**Backend:** FastAPI + SQLite (`journal/`)
- `database.py` — SQLite at `journal/data/trades.db`
- `models.py` — `Trade` SQLAlchemy model with all fields
- `main.py` — REST API + page routes

**Frontend:** 3 HTML pages in `journal/static/`
- `dashboard.html` — equity curve (SVG), 5 stat cards, grade breakdown, recent trades
- `log.html` — 5-step form (setup → checklist → grade/entry → outcome → notes)
- `history.html` — filterable/sortable full trade table, expandable rows, CSV export
- `demo.html` — fully self-contained static preview with 15 sample trades baked in (no server needed — send as file attachment)

### Running Locally
```bash
cd /Users/LeJack/Documents/trading
source .venv/bin/activate
uvicorn journal.main:app --reload --port 8001
```

Venv lives at `/Users/LeJack/Documents/trading/.venv`. Must run from the `trading/` directory (not `trading/journal/`) due to relative imports.

### Key Design Decisions

**3-state rule toggles (Met / Bent / Not Met)** — captures Ben's subjectivity. He bends rules sometimes; this records exactly which ones and when, so patterns can be found later.

**R auto-calculation** — SL pips input auto-populates 1R, lock-in (SL÷3 rounded up), 2R, 3R targets. Removes mental math during logging.

**Direction-aware labels** — checklist labels update when Long/Short is toggled (e.g. "below 13 EMA" vs "above 13 EMA").

**Equity curve** — pure SVG, no external chart libraries. Zero dependencies beyond FastAPI.

### Deployment Plan (Not Yet Done)
- Register `benstrading.com` at Cloudflare Registrar
- Spin up IONOS VPS (Ubuntu 22.04, cheapest tier ~$2–4/mo)
- systemd service + nginx reverse proxy + Cloudflare DNS
- Push updates via git pull on VPS — Jack deploys, Ben just uses the URL

### Trade Data Model
All rule fields stored as `"met"` / `"bent"` / `"not_met"` strings. Boolean fields (shark_fin, dribble) stored as `Boolean`. Result R auto-calculated from `result_pips / stop_loss_pips` on create/update.

---

## Vision & Roadmap

1. **Phase 1 (done):** Intake form — captures trader's full ruleset
2. **Phase 2 (current):** AI agent that reads intake output, scans for valid setups matching exact methodology, sends alerts
3. **Phase 3 (future):** Autonomous execution — TradingView API integration, auto-place orders

---

## Design System

- Dark theme: `#0a0a0a` background, `#111` surface
- Accent: `#c8f064` (lime green)
- Fonts: Syne (display), IBM Plex Mono, IBM Plex Sans
- Components: chips (multi-select), radio cards, text inputs, progress bar

---

## Key Architectural Notes

- Intake form output → agent's system prompt / configuration
- Correlated pair detection is critical (trader's stated downfall)
- Circuit breaker: halt all signals when 6% weekly drawdown hit
- Trade window enforcement: only scan/alert between 11 AM Japan time and 9 AM EST
- TradingView is the platform — any integration will go through TradingView's API or Pine Script webhooks

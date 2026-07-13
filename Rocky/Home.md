---
type: meta
tags: [meta, home, index, catalog]
created: 2026-07-13
updated: 2026-07-13
source: [README.md, memory/trade-outcomes.json, memory/TRADE-LOG.md]
---

# Home

**Rocky** is an autonomous AI swing-trading agent for the Indian market (NSE/BSE), managing a ₹5,00,000 **paper** portfolio. It scores the Nifty 50 + Midcap 150 universe on five momentum factors, enforces a mechanical [[9-Point Buy Gate]] on every entry, and commits every decision to Git. This vault is its second brain — see [[Schema]] for how it is built and maintained.

**Live window:** 2026-05-17 → 2026-06-19. **Current state:** flat (no open positions), portfolio **₹4,85,218** (−2.96% all-time), self-grade **D**, [[Fitness Score]] −0.768. Routines are **paused mid-migration** back to Claude orchestration (era 3, see [[Infrastructure Eras]]). Nine trades closed, 44.4% win rate — the honest verdict is in [[Strategy Verdict]].

## Insights
- [[Strategy Verdict]] — the central thesis: the infrastructure is the asset; the strategy was the experiment, and it failed honestly.
- [[Lessons Learned]] — distilled lessons: trust the walk-forward, the category (not the rule) was wrong, time-exits dominated, one source of truth.
- [[Open Questions]] — genuine unknowns: bull-regime timing, the unreachable 20-trade threshold, max-hold length, record discrepancies, what era 3 changes.

## Strategy
- [[Swing v3]] — the current (paused) strategy: 3–15 day momentum swings; 9 live trades, 44.4% win, −2.96%.
- [[Position Trading v1]] — the original, now-frozen longer-horizon strategy, superseded by Swing v3 on 2026-05-27.
- [[POC v2 Backtest]] — the in-sample proof-of-concept that looked great: +12.31% / +6.66% alpha — and wasn't to be trusted.
- [[Phase B Walk-Forward]] — the overfitting case study: training +9.62% → holdout −6.57%, decision REVERT_TO_BASELINE.
- [[Mean Reversion Experiment]] — rejected counter-trend class: high win rate (60–64%), negative return — the classic mean-reversion trap.
- [[Sector Rotation Experiment]] — rejected top-down class: the most spectacular overfit (train +31% → holdout −9.69%).

## Trades
- [[JSWSTEEL-2026-05-20]] — top-scored metals idea that eked out a quiet +1.60% max_hold win.
- [[BHARTIARTL-2026-05-20]] — highest-conviction entry (80 score, record earnings) that still hard-stopped at −5.24%.
- [[TECHM-2026-05-20]] — lowest-score entry that closed green (+1.47%); the only thesis_broken exit.
- [[MANAPPURAM-2026-05-20]] — started a leader, gapped through the stop to the worst loss (−7.00%).
- [[TATACONSUM-2026-05-20]] — flat-then-fade FMCG hold that hard-stopped at −5.22%.
- [[RADICO-2026-05-20]] — choppy FMCG hold that never got going, max_hold −3.60%.
- [[BAJAJ-AUTO-2026-05-20]] — the cohort's best trade (+3.38%) and its only [[Partial Exit]] — from the lowest score.
- [[HINDALCO-2026-05-21]] — peaked +5.65% just shy of the partial trigger, then rolled to −5.53%.
- [[ADANIPORTS-2026-05-21]] — the steadiest, drama-free hold; the sole MEDIUM catalyst, +0.87%.

## Stocks
- [[JSWSTEEL]] — India's largest private-sector steel producer (Nifty 50, [[Metals]]).
- [[BHARTIARTL]] — India's second-largest telecom operator (Nifty 50, [[Telecom]]).
- [[TECHM]] — IT services and digital-transformation major (Nifty 50, [[IT]]).
- [[MANAPPURAM]] — gold-loan-focused NBFC (Midcap 150, [[Finance]]).
- [[TATACONSUM]] — packaged foods and beverages major (Nifty 50, [[FMCG]]).
- [[RADICO]] — IMFL and premium spirits maker (Midcap 150, [[FMCG]]).
- [[BAJAJ-AUTO]] — two- and three-wheeler manufacturer with a strong export franchise (Nifty 50, [[Auto]]).
- [[HINDALCO]] — aluminium and copper major, owner of Novelis (Nifty 50, [[Metals]]).
- [[ADANIPORTS]] — India's largest private port and logistics operator (Nifty 50, [[Infrastructure]]).

## Sectors
- [[Metals]] — the one sector Rocky ran at the 2-per-sector cap (JSWSTEEL + HINDALCO).
- [[FMCG]] — the other 2-concurrent sector (TATACONSUM + RADICO), right at the Gate 9 cap.
- [[Telecom]] — single-name sector (BHARTIARTL), within the cap.
- [[IT]] — single-name sector (TECHM); a 2nd add (INFY) was weighed but never cleared the gates.
- [[Finance]] — single-name NBFC sector (MANAPPURAM), within the cap.
- [[Auto]] — single-name sector (BAJAJ-AUTO), within the cap.
- [[Infrastructure]] — single-name sector (ADANIPORTS), within the cap.

## Concepts
- [[9-Point Buy Gate]] — the mechanical "9+1" entry filter; all conditions must pass, no discretion.
- [[Catalyst Tiers]] — Gate 3: every entry needs a HARD/MEDIUM/SOFT-classified event driving it.
- [[Swing Score]] — the 5-factor momentum score (0–100); Gate 2 requires ≥ 80.
- [[Regime Detection]] — daily bull/bear/sideways call from Nifty 20d SMA slope; feeds gate 10.
- [[Hard Stop]] — the non-negotiable −5% loss cut (tightened from −7% under v1).
- [[Partial Exit]] — mandatory: sell half at +6%, then tighten the rest's trailing stop.
- [[Trailing Stop]] — the profit-protecting stop that ratchets one way only, never down.
- [[Fitness Score]] — the machine-readable self-grade against `goal.yaml`; live run scored D.
- [[Walk-Forward Validation]] — the anti-overfitting discipline: lock rules, test once on a holdout.
- [[Overfitting]] — the central failure mode: dazzling in-sample, worthless out-of-sample.
- [[India VIX]] — NSE's fear gauge; a risk-off switch that blocks entries when elevated.
- [[FII-DII Flows]] — institutional net buying/selling; heavy FII outflow blocks new longs.

## System
- [[Architecture]] — the design pattern: build the measuring instrument first, swap strategies through it.
- [[Routines]] — the six IST Claude routines (pre-market → weekly-review) that drive the trading day.
- [[Signal Generator]] — `models/signal_generator.py`, the Swing v3 5-factor momentum scorer.
- [[Broker - Upstox]] — `scripts/broker.py`, the Upstox API v2 wrapper; the only path to orders.
- [[Data Sources]] — the free-tier feeds behind every decision (₹0/month infra goal).
- [[Infrastructure Eras]] — three orchestrators (local Claude → GitHub Actions/Gemini → back to Claude), one instrument.

## Journal
- [[Timeline]] — dated milestones across the whole project history.
- [[2026-W21]] — the entries week: all nine opening positions placed 2026-05-20/21.
- [[2026-W22]] — a quiet holding week; positions rode on, zero realised trades.
- [[2026-W23]] — the strategy first showed its downside; first hard stops, grade dropped to D.
- [[2026-W24]] — the mass-exit week; max-hold force-closed the book, 3 → 9 closed trades.
- [[2026-W25]] — a flat, fully-cash last live week; nothing cleared the gate.

## Meta
- [[Schema]] — how this wiki works: layers, conventions, page types, operations.
- [[Log]] — the append-only build-and-ingest operation log.

## The nine live trades

| Symbol | Sector | Entry | Exit | P&L % | Exit reason |
|---|---|---|---|---|---|
| [[JSWSTEEL-2026-05-20\|JSWSTEEL]] | Metals | 2026-05-20 | 2026-06-10 | +1.60% | max_hold |
| [[BHARTIARTL-2026-05-20\|BHARTIARTL]] | Telecom | 2026-05-20 | 2026-06-04 | −5.24% | hard_stop |
| [[TECHM-2026-05-20\|TECHM]] | IT | 2026-05-20 | 2026-05-29 | +1.47% | thesis_broken |
| [[MANAPPURAM-2026-05-20\|MANAPPURAM]] | Finance | 2026-05-20 | 2026-06-10 | −7.00% | max_hold |
| [[TATACONSUM-2026-05-20\|TATACONSUM]] | FMCG | 2026-05-20 | 2026-06-05 | −5.22% | hard_stop |
| [[RADICO-2026-05-20\|RADICO]] | FMCG | 2026-05-20 | 2026-06-10 | −3.60% | max_hold |
| [[BAJAJ-AUTO-2026-05-20\|BAJAJ-AUTO]] | Auto | 2026-05-20 | 2026-06-10 | +3.38% | max_hold |
| [[HINDALCO-2026-05-21\|HINDALCO]] | Metals | 2026-05-21 | 2026-06-11 | −5.53% | max_hold |
| [[ADANIPORTS-2026-05-21\|ADANIPORTS]] | Infrastructure | 2026-05-21 | 2026-06-11 | +0.87% | max_hold |

Win rate **44.4%** (4W / 5L) · avg winner ~+2.15% · avg loser ~−5.27% · EV ≈ **−2.09%/trade**.

The same nine, live-queried for users with the Dataview plugin:

```dataview
TABLE sector, entry_date, exit_date, pnl_pct, exit_reason
FROM "Trades"
SORT entry_date
```

## Start here
- [[Strategy Verdict]] — read this first; it's the whole point.
- [[Timeline]] — the story in dated order.
- [[Schema]] — how the vault is structured and maintained.

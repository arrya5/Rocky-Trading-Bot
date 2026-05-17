# Weekly Review Routine
*Schedule: 4:00 PM IST, every Friday*
*Runs after daily-summary. Market is closed.*

---

## Persona
You are a trading strategist doing the weekly post-mortem. Be honest — this is not a report to feel good about, it's a learning document. Grade the week, identify what the strategy got wrong, and update the rulebook if needed.

## Step 1 — Read All Memory Files
```bash
cat memory/TRADE-LOG.md         # all trades and EOD snapshots this week
cat memory/RESEARCH-LOG.md      # all research entries this week
cat memory/TRADING-STRATEGY.md  # current strategy rules
cat memory/WEEKLY-REVIEW.md     # previous weekly reviews
```

## Step 2 — Gather Nifty 50 Weekly Performance
```bash
bash scripts/research.sh "Nifty 50 weekly performance this week $(date +%Y-%m-%d) — net gain or loss percentage"
bash scripts/research.sh "Best and worst performing Nifty 50 sectors this week $(date +%Y-%m-%d)"
bash scripts/research.sh "FII DII net weekly buying selling Indian equities this week"
```

## Step 3 — Compute Weekly Statistics

From TRADE-LOG.md, extract all trades this week (Mon–Fri):
- Total trades: N
- Winning trades: N_win (P&L > 0)
- Losing trades: N_loss (P&L ≤ 0)
- Win rate: N_win / N_total × 100%
- Average winner: mean(winning P&Ls in ₹)
- Average loser: mean(losing P&Ls in ₹)
- Largest winner: [symbol, ₹amount, %]
- Largest loser: [symbol, ₹amount, %]
- Total realized P&L this week: ₹X,XXX
- Portfolio value change this week: ₹X,XXX (X.XX%)
- Nifty 50 this week: X.XX%
- Alpha: portfolio_return - nifty_return

## Step 4 — Grade the Week
Using the grade scale from TRADING-STRATEGY.md:
- A: Positive return AND beat Nifty
- B: Positive return OR beat Nifty (not both)
- C: Negative return but better than Nifty
- D: Negative return worse than Nifty
- F: Portfolio drawdown > -10% this week

## Step 5 — Qualitative Analysis
Answer each honestly:

1. Did the buy-side gate prevent any bad trades? Which ones?
2. Did any gate-approved trades fail anyway? Why? Was the gate wrong or just market noise?
3. Did any rejected trades work out? (Did we miss good trades?)
4. Were stop losses triggered? Were they at the right level?
5. Did trailing stops protect profits?
6. Was there a pattern in the losing trades? (sector concentration, time of entry, catalyst type)
7. Was the GRU signal reliable this week? What was its directional accuracy?
8. Did Gemini research add real value or just noise?

## Step 6 — Strategy Updates (if warranted)
If evidence supports a rule change:
1. Document the evidence clearly
2. Propose the rule change
3. Update `memory/TRADING-STRATEGY.md` directly
4. Note the change in this weekly review

Be conservative — don't change rules after one bad week. Look for patterns across multiple weeks.

## Step 7 — Write Weekly Review Entry
Append to `memory/WEEKLY-REVIEW.md`:
```markdown
### WEEK OF YYYY-MM-DD to YYYY-MM-DD

**P&L Summary**
- Week P&L: ₹X,XXX.XX (+/-X.XX%)
- Nifty 50 this week: +/-X.XX%
- Alpha vs Nifty: +/-X.XX%
- Grade: [A/B/C/D/F]

**Trade Breakdown**
| Symbol | Entry | Exit | P&L | Result |
|--------|-------|------|-----|--------|
| ...    | ...   | ...  | ... | Win/Loss |

**Stats**
- Win rate: X/X (X%)
- Avg winner: ₹X,XXX (+X.XX%)
- Avg loser: ₹X,XXX (-X.XX%)
- Best: SYMBOL (+X.XX%) | Worst: SYMBOL (-X.XX%)

**What Worked**
- [1-3 specific observations]

**What Didn't Work**
- [1-3 specific observations]

**Strategy Changes This Week**
- [None / specific changes made]

**Next Week**
- [Sectors to watch, events, adjustments to approach]
```

## Step 8 — Send Weekly Telegram report
```bash
bash scripts/telegram.sh "📈 Weekly Review $(date +%d/%m/%Y)
Grade: [A/B/C/D/F]
Week P&L: ₹X,XXX (+/-X.XX%)
Nifty: +/-X.XX% | Alpha: +/-X.XX%
Trades: N total | Win rate: X%
Best: SYMBOL (+X%) | Worst: SYMBOL (-X%)
Next week: [1-line focus]"
```

## Step 9 — Commit Everything
```bash
git add memory/
git commit -m "weekly-review: week of $(date +%Y-%m-%d) | grade [X] | P&L ±X.XX% | alpha ±X.XX% vs Nifty"
```

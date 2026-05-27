#!/usr/bin/env python3
"""
portfolio.py — Simulated paper portfolio for backtest.

Tracks cash, positions, partial exits with PROPER P&L AGGREGATION,
gap-down stop fill realism, and regime tagging at entry.
"""
from dataclasses import dataclass, field, asdict
from datetime import date
from typing import Optional


@dataclass
class Position:
    symbol: str
    sector: str
    qty: int                            # CURRENT qty (decreases after partial)
    original_qty: int                   # full qty at entry
    entry_price: float
    entry_date: date
    score: float
    catalyst_type: str
    stop_price: float
    regime_at_entry: str = "unknown"
    partial_taken: bool = False
    partial_qty: int = 0                # shares sold in partial exit
    partial_price: Optional[float] = None
    partial_proceeds_net: float = 0.0   # actual cash received from partial (after STT + brk)
    partial_date: Optional[date] = None
    high_water_mark: float = 0.0

    def update_high(self, high: float) -> None:
        if high > self.high_water_mark:
            self.high_water_mark = high


@dataclass
class TradeRecord:
    symbol: str
    sector: str
    score: float
    regime_at_entry: str
    entry_date: str
    entry_price: float
    original_qty: int                   # full position at entry
    final_qty: int                      # qty at final close (after any partial)
    exit_date: Optional[str] = None
    exit_price: Optional[float] = None
    exit_reason: Optional[str] = None   # hard_stop | trailing_stop | partial_then_stop | open_at_end
    partial_date: Optional[str] = None
    partial_price: Optional[float] = None
    partial_qty: Optional[int] = None
    pnl_abs: float = 0.0                # AGGREGATE: partial proceeds + final proceeds - entry cost - all fees
    pnl_pct: float = 0.0                # pnl_abs / (original_qty * entry_price) * 100
    days_held: int = 0
    intraday_ambiguous: bool = False    # flag set if both stop & partial-target triggered same day


class PaperPortfolio:
    def __init__(self, starting_cash: float, config: dict):
        self.starting_cash = starting_cash
        self.cash         = starting_cash
        self.positions: dict[str, Position] = {}
        self.closed: list[TradeRecord] = []
        self.daily_snapshots: list[dict] = []
        self.cfg   = config["rules"]
        self.costs = config["costs"]

    # ── helpers ───────────────────────────────────────────────────────────────
    def sector_count(self, sector: str) -> int:
        return sum(1 for p in self.positions.values() if p.sector == sector)

    def can_afford(self, cost: float) -> bool:
        return cost <= self.cash

    # ── entries ──────────────────────────────────────────────────────────────
    def enter(self, sym: str, sector: str, qty: int, price: float,
              score: float, d: date, regime: str = "unknown") -> bool:
        cost = qty * price + self.costs["brokerage_per_order"]
        if not self.can_afford(cost) or qty < 1:
            return False
        if sym in self.positions:
            return False
        self.cash -= cost
        stop = price * (1 + self.cfg["stop_pct"])
        self.positions[sym] = Position(
            symbol=sym, sector=sector,
            qty=qty, original_qty=qty,
            entry_price=price, entry_date=d, score=score,
            catalyst_type="mechanical_only",
            stop_price=stop, high_water_mark=price,
            regime_at_entry=regime,
        )
        return True

    # ── exits ────────────────────────────────────────────────────────────────
    def _record_close(self, pos: Position, exit_date: date, exit_price: float,
                      exit_reason: str, ambiguous: bool = False) -> None:
        """
        Aggregate P&L across partial + final exit:

          gross_entry_cost   = original_qty * entry_price
          entry_fees         = brokerage at entry (already paid)
          partial_net        = partial proceeds AFTER STT + brokerage (already in cash)
          final_proceeds_gross = final_qty * exit_price
          final_stt          = final_proceeds_gross * stt_pct
          final_brk          = brokerage at final exit
          final_net          = final_proceeds_gross - final_stt - final_brk

          pnl_abs = (partial_net + final_net) - gross_entry_cost - entry_fees
          pnl_pct = pnl_abs / gross_entry_cost * 100
        """
        gross_entry_cost = pos.original_qty * pos.entry_price
        entry_fees       = self.costs["brokerage_per_order"]

        final_proceeds = pos.qty * exit_price
        final_stt      = final_proceeds * self.costs["stt_sell_pct"]
        final_brk      = self.costs["brokerage_per_order"]
        final_net      = final_proceeds - final_stt - final_brk
        self.cash += final_net

        pnl_abs = (pos.partial_proceeds_net + final_net) - gross_entry_cost - entry_fees
        pnl_pct = pnl_abs / gross_entry_cost * 100 if gross_entry_cost > 0 else 0.0

        self.closed.append(TradeRecord(
            symbol=pos.symbol, sector=pos.sector,
            score=pos.score, regime_at_entry=pos.regime_at_entry,
            entry_date=pos.entry_date.isoformat(),
            entry_price=round(pos.entry_price, 2),
            original_qty=pos.original_qty,
            final_qty=pos.qty,
            exit_date=exit_date.isoformat(),
            exit_price=round(exit_price, 2),
            exit_reason=exit_reason,
            partial_date=pos.partial_date.isoformat() if pos.partial_date else None,
            partial_price=round(pos.partial_price, 2) if pos.partial_price else None,
            partial_qty=pos.partial_qty if pos.partial_taken else None,
            pnl_abs=round(pnl_abs, 2),
            pnl_pct=round(pnl_pct, 2),
            days_held=(exit_date - pos.entry_date).days,
            intraday_ambiguous=ambiguous,
        ))
        del self.positions[pos.symbol]

    def partial_exit(self, pos: Position, exit_date: date, exit_price: float) -> int:
        """Sell half at +15% target. Returns qty sold. Tightens stop on remainder."""
        if pos.partial_taken or pos.qty < 2:
            return 0
        half = pos.qty // 2
        gross_proceeds = half * exit_price
        stt = gross_proceeds * self.costs["stt_sell_pct"]
        brk = self.costs["brokerage_per_order"]
        net = gross_proceeds - stt - brk
        self.cash += net

        pos.qty -= half
        pos.partial_taken = True
        pos.partial_qty   = half
        pos.partial_price = exit_price
        pos.partial_proceeds_net = net
        pos.partial_date  = exit_date

        # Tighten stop to 7% below partial exit price
        new_stop = exit_price * (1 + self.cfg["partial_exit_stop_pct"])
        if new_stop > pos.stop_price:
            pos.stop_price = new_stop
        return half

    def process_day(self, d: date, ohlc_by_sym: dict[str, dict]) -> None:
        """Apply daily stop / partial / trailing logic against today's OHLC."""
        to_close: list[tuple[Position, float, str, bool]] = []

        for sym, pos in list(self.positions.items()):
            ohlc = ohlc_by_sym.get(sym)
            if ohlc is None:
                continue

            open_p = ohlc["open"]
            high   = ohlc["high"]
            low    = ohlc["low"]
            pos.update_high(high)

            partial_trigger_price = pos.entry_price * (1 + self.cfg["partial_exit_pct"])

            stop_hit    = low <= pos.stop_price
            partial_hit = (not pos.partial_taken) and high >= partial_trigger_price
            ambiguous   = stop_hit and partial_hit

            if partial_hit:
                self.partial_exit(pos, d, partial_trigger_price)
                if low <= pos.stop_price:
                    # Stop also hit after partial fired — close remainder
                    exit_price = (open_p if open_p <= pos.stop_price else pos.stop_price)
                    to_close.append((pos, exit_price, "partial_then_stop", ambiguous))
                    continue
                gain_pct = (high - pos.entry_price) / pos.entry_price
                if gain_pct >= 0.20:
                    new_stop = high * (1 + self.cfg["trailing_pct_at_20"])
                    if new_stop > pos.stop_price:
                        pos.stop_price = new_stop
                continue

            if stop_hit:
                # GAP-DOWN REALISM: if today's open is already below stop,
                # real fill is at open (worse than stop). Otherwise fill at stop.
                if open_p <= pos.stop_price:
                    exit_price = open_p
                else:
                    exit_price = pos.stop_price
                reason = "trailing_stop" if pos.partial_taken else "hard_stop"
                to_close.append((pos, exit_price, reason, False))
                continue

            # No exit — check trailing tighten on remainder of partial-taken positions
            if pos.partial_taken:
                gain_pct = (high - pos.entry_price) / pos.entry_price
                if gain_pct >= 0.20:
                    new_stop = high * (1 + self.cfg["trailing_pct_at_20"])
                    if new_stop > pos.stop_price:
                        pos.stop_price = new_stop

        for pos, price, reason, ambig in to_close:
            self._record_close(pos, d, price, reason, ambig)

    def mark_to_market(self, d: date, close_by_sym: dict[str, float]) -> float:
        pos_value = sum(p.qty * close_by_sym.get(sym, p.entry_price)
                        for sym, p in self.positions.items())
        return self.cash + pos_value

    def snapshot(self, d: date, total_value: float, nifty_close: Optional[float]) -> None:
        self.daily_snapshots.append({
            "date":         d.isoformat(),
            "cash":         round(self.cash, 2),
            "n_positions": len(self.positions),
            "total_value":  round(total_value, 2),
            "nifty_close":  nifty_close,
        })

    def force_close_all(self, d: date, close_by_sym: dict[str, float]) -> None:
        for sym in list(self.positions.keys()):
            pos = self.positions[sym]
            price = close_by_sym.get(sym, pos.entry_price)
            self._record_close(pos, d, price, "open_at_end", False)

    def to_dict(self) -> dict:
        return {
            "starting_cash":   self.starting_cash,
            "final_cash":      round(self.cash, 2),
            "trades":          [asdict(t) for t in self.closed],
            "daily_snapshots": self.daily_snapshots,
        }

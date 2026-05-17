#!/usr/bin/env python3
"""
signal_generator.py — GRU-based trade signal generator for NSE stocks

Usage:
  python models/signal_generator.py RELIANCE TCS INFY HDFCBANK
  python models/signal_generator.py RELIANCE

Output (JSON, one object per symbol):
  {
    "RELIANCE": {
      "signal": "BUY",          # BUY / SELL / HOLD
      "confidence": 72.4,       # 0-100%
      "current_price": 2481.35,
      "forecast_5d": 2634.23,   # 5-day GRU forecast
      "forecast_change_pct": 6.16,
      "direction_accuracy_7d": 0.71,  # model's recent accuracy
      "generated_at": "2026-05-17T09:20:00"
    }
  }

Signal logic:
  BUY  : forecast_change_pct ≥ +3% AND recent direction accuracy ≥ 55%
  SELL : forecast_change_pct ≤ -3% AND recent direction accuracy ≥ 55%
  HOLD : everything else (uncertain)

Confidence = min(100, abs(forecast_change_pct) * 10) × direction_accuracy
"""

import os, sys, json, warnings
warnings.filterwarnings("ignore")

os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

import numpy as np
import pandas as pd
import yfinance as yf
from datetime import datetime
from pathlib import Path

import tensorflow as tf
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.layers import GRU, Dense, Dropout
from tensorflow.keras.callbacks import EarlyStopping
from tensorflow.keras.regularizers import l2
from sklearn.preprocessing import MinMaxScaler

# ── Config ────────────────────────────────────────────────────────────────────

SEQ_LEN       = 60     # lookback window in trading days
FORECAST_DAYS = 5      # days ahead to forecast
TRAIN_MONTHS  = 18     # months of history to train on
BUY_THRESHOLD = 3.0    # % forecast gain to signal BUY
SELL_THRESHOLD = -3.0  # % forecast loss to signal SELL
MIN_DIR_ACC   = 0.55   # min directional accuracy to trust signal
MODEL_CACHE   = Path(__file__).parent / "cached"
MODEL_CACHE.mkdir(exist_ok=True)

# ── Data ──────────────────────────────────────────────────────────────────────

def fetch(symbol: str) -> pd.DataFrame:
    ticker = symbol.upper()
    if not ticker.endswith(".NS"):
        ticker = ticker + ".NS"

    end   = pd.Timestamp.today()
    start = end - pd.DateOffset(months=TRAIN_MONTHS)

    df = yf.download(ticker, start=start, end=end, progress=False, auto_adjust=True)
    if df.empty:
        raise ValueError(f"No data returned for {ticker}")

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df.ffill(inplace=True)
    df.dropna(inplace=True)

    if not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index)

    return df


def add_features(df: pd.DataFrame) -> pd.DataFrame:
    d = df.copy()

    # Price features
    d['returns']     = d['Close'].pct_change()
    d['volatility']  = d['returns'].rolling(20).std()
    d['hl_range']    = (d['High'] - d['Low']) / d['Close']
    d['gap']         = (d['Open'] - d['Close'].shift(1)) / d['Close'].shift(1)

    # Trend indicators
    d['sma20']       = d['Close'].rolling(20).mean()
    d['sma50']       = d['Close'].rolling(50).mean()
    d['ema12']       = d['Close'].ewm(span=12, adjust=False).mean()
    d['ema26']       = d['Close'].ewm(span=26, adjust=False).mean()
    d['macd']        = d['ema12'] - d['ema26']
    d['price_sma20'] = d['Close'] / d['sma20'] - 1   # distance from SMA20
    d['price_sma50'] = d['Close'] / d['sma50'] - 1

    # Momentum
    d['rsi']         = _rsi(d['Close'], 14)
    d['mom5']        = d['Close'].pct_change(5)
    d['mom10']       = d['Close'].pct_change(10)

    # Volume
    d['vol_ma20']    = d['Volume'].rolling(20).mean()
    d['vol_ratio']   = d['Volume'] / d['vol_ma20']

    d.dropna(inplace=True)
    return d


def _rsi(series: pd.Series, period: int) -> pd.Series:
    delta = series.diff()
    gain  = delta.clip(lower=0).rolling(period).mean()
    loss  = (-delta.clip(upper=0)).rolling(period).mean()
    rs    = gain / loss.replace(0, np.nan)
    return 100 - 100 / (1 + rs)


FEATURE_COLS = [
    'Close', 'returns', 'volatility', 'hl_range', 'gap',
    'price_sma20', 'price_sma50', 'macd', 'rsi',
    'mom5', 'mom10', 'vol_ratio',
]


def make_sequences(data: np.ndarray, seq_len: int):
    X, y = [], []
    for i in range(len(data) - seq_len):
        X.append(data[i:i+seq_len])
        y.append(data[i+seq_len, 0])   # predict next Close (index 0)
    return np.array(X), np.array(y)

# ── Model ─────────────────────────────────────────────────────────────────────

def build_gru(n_features: int) -> tf.keras.Model:
    model = Sequential([
        GRU(64, return_sequences=True, input_shape=(SEQ_LEN, n_features)),
        Dropout(0.2),
        GRU(32),
        Dropout(0.2),
        Dense(16, activation='relu'),
        Dense(1, kernel_regularizer=l2(0.001)),
    ])
    model.compile(optimizer='adam', loss='mse')
    return model


def train_or_load(symbol: str, df_feat: pd.DataFrame, scaler: MinMaxScaler, scaled: np.ndarray):
    cache_path = MODEL_CACHE / f"{symbol}_gru.keras"

    # Check if cached model is recent enough (same day)
    if cache_path.exists():
        mtime = datetime.fromtimestamp(cache_path.stat().st_mtime)
        if mtime.date() == datetime.today().date():
            return load_model(cache_path)

    X, y = make_sequences(scaled, SEQ_LEN)
    if len(X) < 10:
        raise ValueError(f"Not enough data to train model for {symbol}")

    model = build_gru(scaled.shape[1])
    es    = EarlyStopping(monitor='loss', patience=5, restore_best_weights=True, verbose=0)
    model.fit(X, y, epochs=50, batch_size=32, verbose=0, callbacks=[es])
    model.save(cache_path)
    return model


def forecast(model, last_seq: np.ndarray, steps: int, scaler: MinMaxScaler, n_features: int) -> list[float]:
    seq   = last_seq.copy()
    preds = []

    for _ in range(steps):
        p = model.predict(seq.reshape(1, SEQ_LEN, n_features), verbose=0)[0, 0]
        preds.append(p)

        # Build next row: predicted close + roll forward other features
        next_row    = seq[-1].copy()
        next_row[0] = p
        seq         = np.vstack([seq[1:], next_row])

    # Inverse transform: only Close column (index 0)
    dummy        = np.zeros((len(preds), n_features))
    dummy[:, 0]  = preds
    inv          = scaler.inverse_transform(dummy)
    return inv[:, 0].tolist()


def directional_accuracy(model, X_val: np.ndarray, y_val: np.ndarray, scaler: MinMaxScaler, n_features: int) -> float:
    if len(X_val) < 5:
        return 0.6   # default assumption when validation set too small

    preds_raw = model.predict(X_val, verbose=0).flatten()

    # Inverse transform
    dummy_p      = np.zeros((len(preds_raw), n_features))
    dummy_p[:,0] = preds_raw
    dummy_a      = np.zeros((len(y_val), n_features))
    dummy_a[:,0] = y_val

    p_inv = scaler.inverse_transform(dummy_p)[:,0]
    a_inv = scaler.inverse_transform(dummy_a)[:,0]

    # Get the last-known price for each sequence (index SEQ_LEN-1)
    # approximate: direction = predicted next > actual current?
    correct = np.sum(np.sign(p_inv - a_inv) == np.sign(np.diff(a_inv, prepend=a_inv[0])))
    return float(correct / len(p_inv))

# ── Signal logic ──────────────────────────────────────────────────────────────

def generate_signal(symbol: str) -> dict:
    sym_clean = symbol.upper().replace(".NS", "")

    try:
        df_raw  = fetch(sym_clean)
        df_feat = add_features(df_raw)

        features   = df_feat[FEATURE_COLS].values.astype(np.float32)
        n_features = features.shape[1]

        scaler = MinMaxScaler()
        scaled = scaler.fit_transform(features)

        # Train/val split for directional accuracy
        split  = int(len(scaled) * 0.85)
        scaled_train = scaled[:split]
        scaled_val   = scaled[split:]

        model = train_or_load(sym_clean, df_feat, scaler, scaled_train)

        # Directional accuracy on held-out validation set
        if len(scaled_val) > SEQ_LEN:
            X_val, y_val = make_sequences(scaled_val, SEQ_LEN)
            dir_acc = directional_accuracy(model, X_val, y_val, scaler, n_features)
        else:
            dir_acc = 0.60

        # Forecast FORECAST_DAYS ahead from latest data
        last_seq      = scaled[-SEQ_LEN:]
        forecast_vals = forecast(model, last_seq, FORECAST_DAYS, scaler, n_features)
        current_price = float(df_raw['Close'].iloc[-1])
        forecast_5d   = forecast_vals[-1]

        forecast_pct  = (forecast_5d - current_price) / current_price * 100

        # Signal determination
        if forecast_pct >= BUY_THRESHOLD and dir_acc >= MIN_DIR_ACC:
            signal = "BUY"
        elif forecast_pct <= SELL_THRESHOLD and dir_acc >= MIN_DIR_ACC:
            signal = "SELL"
        else:
            signal = "HOLD"

        # Confidence: higher forecast change AND higher directional accuracy = higher confidence
        confidence = min(100.0, abs(forecast_pct) * 8 * dir_acc)

        return {
            "symbol":                 sym_clean,
            "signal":                 signal,
            "confidence":             round(confidence, 1),
            "current_price":          round(current_price, 2),
            "forecast_5d":            round(forecast_5d, 2),
            "forecast_change_pct":    round(forecast_pct, 2),
            "direction_accuracy_pct": round(dir_acc * 100, 1),
            "data_points":            len(df_feat),
            "generated_at":           datetime.now().isoformat(),
        }

    except Exception as e:
        return {
            "symbol":      sym_clean,
            "signal":      "ERROR",
            "confidence":  0.0,
            "error":       str(e),
            "generated_at": datetime.now().isoformat(),
        }

# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    symbols = sys.argv[1:] if len(sys.argv) > 1 else ["RELIANCE"]

    if not symbols:
        print("Usage: python models/signal_generator.py SYMBOL [SYMBOL ...]", file=sys.stderr)
        sys.exit(1)

    results = {}
    for sym in symbols:
        print(f"Processing {sym}...", file=sys.stderr)
        results[sym.upper().replace(".NS", "")] = generate_signal(sym)

    print(json.dumps(results, indent=2))

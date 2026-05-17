import warnings
warnings.filterwarnings("ignore")
os_env_set = True

import os
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

import threading, joblib, logging
import numpy as np
import pandas as pd
import yfinance as yf
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from datetime import datetime
from statsmodels.tsa.arima.model import ARIMA
from scipy.optimize import minimize

import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, LSTM, GRU, Dropout
from tensorflow.keras.callbacks import EarlyStopping
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.regularizers import l2
from sklearn.preprocessing import MinMaxScaler
from sklearn.ensemble import RandomForestRegressor
import xgboost as xgb
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

import ta
from ta.trend import SMAIndicator, EMAIndicator, MACD
from ta.momentum import RSIIndicator, StochasticOscillator
from ta.volatility import BollingerBands
from ta.volume import OnBalanceVolumeIndicator

physical_devices = tf.config.list_physical_devices('GPU')
model_dir = 'models'
plot_dir = 'plots'
os.makedirs(model_dir, exist_ok=True)
os.makedirs(plot_dir, exist_ok=True)

TICKER = "AAPL"
TRAIN_RATIO = 0.8
SEQ_LEN = 60

# ── Data ─────────────────────────────────────────────────────────────────────

def download(ticker, years=3):
    end = pd.Timestamp.today()
    start = end - pd.DateOffset(years=years)
    df = yf.download(ticker, start=start, end=end, progress=False)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df.ffill(inplace=True)
    df.interpolate(method='linear', inplace=True)
    df.dropna(inplace=True)
    if not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index)
    return df

def add_indicators(df):
    d = df.copy()
    d['SMA20']  = SMAIndicator(close=d['Close'], window=20).sma_indicator()
    d['SMA50']  = SMAIndicator(close=d['Close'], window=50).sma_indicator()
    d['EMA12']  = EMAIndicator(close=d['Close'], window=12).ema_indicator()
    macd = MACD(close=d['Close'])
    d['MACD']   = macd.macd()
    rsi  = RSIIndicator(close=d['Close'])
    d['RSI']    = rsi.rsi()
    bb   = BollingerBands(close=d['Close'])
    d['BB_Width'] = (bb.bollinger_hband() - bb.bollinger_lband()) / bb.bollinger_mavg()
    obv  = OnBalanceVolumeIndicator(close=d['Close'], volume=d['Volume'])
    d['OBV']    = obv.on_balance_volume()
    d['Returns'] = d['Close'].pct_change() * 100
    d['Volatility'] = d['Returns'].rolling(20).std()
    d['Volume_MA'] = d['Volume'].rolling(20).mean()
    d.dropna(inplace=True)
    return d

def make_sequences(data, seq_len):
    X, y = [], []
    for i in range(len(data) - seq_len):
        X.append(data[i:i+seq_len])
        y.append(data[i+seq_len])
    return np.array(X), np.array(y)

# ── Models ────────────────────────────────────────────────────────────────────

def run_arima(train_close, horizon):
    log_s = np.log(train_close)
    m = ARIMA(log_s, order=(0,1,0)).fit()
    return np.exp(m.forecast(steps=horizon)).values

def run_lstm(train_close, horizon):
    scaler = MinMaxScaler()
    scaled = scaler.fit_transform(train_close.values.reshape(-1,1))
    X, y = make_sequences(scaled, SEQ_LEN)
    X = X.reshape(X.shape[0], X.shape[1], 1)
    model = Sequential([
        LSTM(50, return_sequences=True, input_shape=(SEQ_LEN,1)),
        Dropout(0.2),
        LSTM(50),
        Dropout(0.2),
        Dense(1, kernel_regularizer=l2(0.001))
    ])
    model.compile(optimizer='adam', loss='mse')
    es = EarlyStopping(monitor='loss', patience=5, restore_best_weights=True)
    model.fit(X, y, epochs=50, batch_size=32, verbose=0, callbacks=[es])
    seq = scaled[-SEQ_LEN:].copy()
    preds = []
    for _ in range(horizon):
        p = model.predict(seq.reshape(1,SEQ_LEN,1), verbose=0)[0,0]
        preds.append(p)
        seq = np.append(seq[1:], [[p]], axis=0)
    return scaler.inverse_transform(np.array(preds).reshape(-1,1)).flatten()

def run_gru(train_close, horizon):
    scaler = MinMaxScaler()
    scaled = scaler.fit_transform(train_close.values.reshape(-1,1))
    X, y = make_sequences(scaled, SEQ_LEN)
    X = X.reshape(X.shape[0], X.shape[1], 1)
    model = Sequential([
        GRU(50, return_sequences=True, input_shape=(SEQ_LEN,1)),
        Dropout(0.2),
        GRU(50),
        Dropout(0.2),
        Dense(1, kernel_regularizer=l2(0.001))
    ])
    model.compile(optimizer='adam', loss='mse')
    es = EarlyStopping(monitor='loss', patience=5, restore_best_weights=True)
    model.fit(X, y, epochs=50, batch_size=32, verbose=0, callbacks=[es])
    seq = scaled[-SEQ_LEN:].copy()
    preds = []
    for _ in range(horizon):
        p = model.predict(seq.reshape(1,SEQ_LEN,1), verbose=0)[0,0]
        preds.append(p)
        seq = np.append(seq[1:], [[p]], axis=0)
    return scaler.inverse_transform(np.array(preds).reshape(-1,1)).flatten()

def run_rf(train_df, horizon):
    d = add_indicators(train_df)
    for lag in range(1,6):
        d[f'lag_{lag}'] = d['Close'].shift(lag)
    d.dropna(inplace=True)
    feat = [f'lag_{i}' for i in range(1,6)] + ['SMA20','SMA50','RSI','MACD','Volume_MA']
    X = d[feat].values
    y = d['Close'].shift(-1).dropna().values
    X = X[:len(y)]
    m = RandomForestRegressor(n_estimators=200, n_jobs=-1, random_state=42)
    m.fit(X, y)
    last = d[feat].iloc[-1:].values
    preds = []
    for _ in range(horizon):
        p = m.predict(last)[0]
        preds.append(p)
        new_lags = np.roll(last[0,:5],1); new_lags[0] = p
        last = np.hstack((new_lags, last[0,5:])).reshape(1,-1)
    return preds

def run_xgb(train_df, horizon):
    d = add_indicators(train_df)
    for lag in range(1,6):
        d[f'lag_{lag}'] = d['Close'].shift(lag)
    d['Target'] = d['Close'].shift(-1)
    d.dropna(inplace=True)
    feat = [f'lag_{i}' for i in range(1,6)] + ['SMA20','SMA50','RSI','MACD','Volume_MA']
    X = d[feat].values; y = d['Target'].values
    m = xgb.XGBRegressor(n_estimators=200, learning_rate=0.1, random_state=42, verbosity=0)
    m.fit(X, y)
    last = d[feat].iloc[-1:].values
    preds = []
    for _ in range(horizon):
        p = m.predict(last)[0]
        preds.append(p)
        new_lags = np.roll(last[0,:5],1); new_lags[0] = p
        last = np.hstack((new_lags, last[0,5:])).reshape(1,-1)
    return preds

# ── Metrics ───────────────────────────────────────────────────────────────────

def metrics(actual, predicted, name):
    a = np.array(actual[:len(predicted)], dtype=float)
    p = np.array(predicted[:len(a)], dtype=float)
    rmse  = np.sqrt(mean_squared_error(a, p))
    mae   = mean_absolute_error(a, p)
    mape  = np.mean(np.abs((a - p) / a)) * 100
    r2    = r2_score(a, p)
    dir_acc = np.mean(np.sign(np.diff(a)) == np.sign(np.diff(p))) * 100
    print(f"\n{'='*45}")
    print(f"  Model: {name}")
    print(f"{'='*45}")
    print(f"  RMSE       : ${rmse:.2f}")
    print(f"  MAE        : ${mae:.2f}")
    print(f"  MAPE       : {mape:.2f}%")
    print(f"  R²         : {r2:.4f}")
    print(f"  Direction  : {dir_acc:.1f}% correct")
    return dict(name=name, rmse=rmse, mae=mae, mape=mape, r2=r2, dir_acc=dir_acc, pred=p)

# ── Main ──────────────────────────────────────────────────────────────────────

print(f"\n{'#'*50}")
print(f"  Evaluating notebook models on {TICKER}")
print(f"{'#'*50}\n")

df = download(TICKER)
print(f"Data: {df.index[0].date()} to {df.index[-1].date()} | {len(df)} trading days")

n = len(df)
split = int(n * TRAIN_RATIO)
train = df.iloc[:split]
test  = df.iloc[split:]
horizon = min(len(test), 30)

print(f"Train: {len(train)} rows | Test: {len(test)} rows | Horizon: {horizon} days\n")

actual = test['Close'].iloc[:horizon].values.astype(float)
results = []

# ARIMA
print("Running ARIMA...", end=' ', flush=True)
try:
    p = run_arima(train['Close'], horizon)
    results.append(metrics(actual, p, 'ARIMA'))
    print("done")
except Exception as e:
    print(f"FAILED: {e}")

# LSTM
print("Running LSTM (training ~50 epochs)...", end=' ', flush=True)
try:
    p = run_lstm(train['Close'], horizon)
    results.append(metrics(actual, p, 'LSTM'))
    print("done")
except Exception as e:
    print(f"FAILED: {e}")

# GRU
print("Running GRU (training ~50 epochs)...", end=' ', flush=True)
try:
    p = run_gru(train['Close'], horizon)
    results.append(metrics(actual, p, 'GRU'))
    print("done")
except Exception as e:
    print(f"FAILED: {e}")

# Random Forest
print("Running Random Forest...", end=' ', flush=True)
try:
    p = run_rf(train.copy(), horizon)
    results.append(metrics(actual, p, 'RandomForest'))
    print("done")
except Exception as e:
    print(f"FAILED: {e}")

# XGBoost
print("Running XGBoost...", end=' ', flush=True)
try:
    p = run_xgb(train.copy(), horizon)
    results.append(metrics(actual, p, 'XGBoost'))
    print("done")
except Exception as e:
    print(f"FAILED: {e}")

# Ensemble
print("\nBuilding Ensemble (average of all models)...")
if results:
    all_preds = np.array([r['pred'] for r in results])
    ens = np.mean(all_preds, axis=0)
    results.append(metrics(actual, ens, 'ENSEMBLE'))

# ── Summary table ─────────────────────────────────────────────────────────────
print(f"\n\n{'='*65}")
print(f"  FINAL LEADERBOARD — {TICKER} | 30-day horizon | train/test 80/20")
print(f"{'='*65}")
print(f"  {'Model':<15} {'RMSE':>8} {'MAE':>8} {'MAPE':>8} {'R²':>8} {'Dir%':>7}")
print(f"  {'-'*57}")
for r in sorted(results, key=lambda x: x['rmse']):
    print(f"  {r['name']:<15} ${r['rmse']:>6.2f}  ${r['mae']:>6.2f}  {r['mape']:>6.2f}%  {r['r2']:>6.4f}  {r['dir_acc']:>5.1f}%")
print(f"{'='*65}")

# ── Plot all models vs actual ─────────────────────────────────────────────────
forecast_dates = test.index[:horizon]
plt.figure(figsize=(14,7))
plt.plot(forecast_dates, actual, 'k-', linewidth=2.5, label='Actual', zorder=10)
colors = ['#e74c3c','#3498db','#2ecc71','#f39c12','#9b59b6','#1abc9c']
for i, r in enumerate(results):
    ls = '--' if r['name'] != 'ENSEMBLE' else '-'
    lw = 1.5 if r['name'] != 'ENSEMBLE' else 2.5
    plt.plot(forecast_dates[:len(r['pred'])], r['pred'], ls, color=colors[i%len(colors)], linewidth=lw, label=r['name'])
plt.title(f"{TICKER} — All Models vs Actual (30-day test horizon)", fontsize=14)
plt.xlabel("Date"); plt.ylabel("Price ($)")
plt.legend(); plt.grid(True, alpha=0.3); plt.tight_layout()
plt.savefig(f"{plot_dir}/{TICKER}_all_models_comparison.png", dpi=150)
print(f"\nComparison chart saved to {plot_dir}/{TICKER}_all_models_comparison.png")

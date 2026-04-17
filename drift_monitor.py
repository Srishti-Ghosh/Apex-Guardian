import os
import asyncio
from collections import deque
import numpy as np
from scipy.stats import ks_2samp
from dotenv import load_dotenv
from faststream import FastStream
from faststream.kafka import KafkaBroker

load_dotenv()

broker = KafkaBroker(os.getenv("REDPANDA_BROKERS", "localhost:19092"))
app = FastStream(broker)

WINDOW_SIZE = 200
HALF_WINDOW = WINDOW_SIZE // 2
P_VALUE_THRESHOLD = 0.05
PSI_THRESHOLD = 0.25 # Model Drift threshold

price_buffers = {
    "BTC/USD": deque(maxlen=WINDOW_SIZE),
    "ETH/USD": deque(maxlen=WINDOW_SIZE),
    "LTC/USD": deque(maxlen=WINDOW_SIZE)
}

def calculate_psi(expected, actual, buckets=10):
    """Calculates Population Stability Index (PSI)"""
    def scale_by_range(data, min_val, max_val):
        # Add 1e-6 to avoid division by zero
        return (np.histogram(data, bins=buckets, range=(min_val, max_val))[0] / len(data)) + 1e-6

    min_val, max_val = min(expected.min(), actual.min()), max(expected.max(), actual.max())
    e_perc = scale_by_range(expected, min_val, max_val)
    a_perc = scale_by_range(actual, min_val, max_val)
    
    return np.sum((a_perc - e_perc) * np.log(a_perc / e_perc))

@broker.subscriber("market-live", group_id="drift-monitor-v3", auto_offset_reset="latest")
async def monitor_model_drift(msg: dict):
    if "status" in msg: return

    symbol = msg["symbol"]
    price = float(msg["price"])
    if symbol not in price_buffers: return

    buffer = price_buffers[symbol]
    
    # 1. Z-SCORE CHECK (Real-time single tick validation)
    if len(buffer) > 50: # Need some baseline for standard deviation
        mean, std = np.mean(buffer), np.std(buffer)
        z_score = abs(price - mean) / std if std > 0 else 0
        if z_score > 3.5:
            print(f"⚠️ DATA WARNING [{symbol}]: Potential fat-finger trade! Z-Score: {z_score:.2f}")

    buffer.append(price)

    # 2. DISTRIBUTION & DRIFT CHECKS (Window validation)
    if len(buffer) == WINDOW_SIZE:
        data = np.array(buffer)
        baseline_dist = data[:HALF_WINDOW]
        current_dist = data[HALF_WINDOW:]

        # Run KS-Test
        ks_stat, p_value = ks_2samp(baseline_dist, current_dist)
        
        # Run PSI Test
        psi = calculate_psi(baseline_dist, current_dist)

        if p_value < P_VALUE_THRESHOLD or psi > PSI_THRESHOLD:
            print(f"🚨 REGIME SHIFT [{symbol}] | PSI: {psi:.4f} | KS p-value: {p_value:.4f}")
            buffer.clear() # Reset window after an alert
        else:
            print(f"📊 {symbol} Stable | PSI: {psi:.4f} | KS p-value: {p_value:.4f}")

if __name__ == "__main__":
    print("🧠 Apex-Guardian Advanced Quant Engine live...")
    asyncio.run(app.run())
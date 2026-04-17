import os
import asyncio
from collections import deque
import numpy as np
from datetime import datetime
from scipy.stats import ks_2samp
from dotenv import load_dotenv
from faststream import FastStream
from faststream.kafka import KafkaBroker
import clickhouse_connect

load_dotenv()

# ClickHouse connection
ch_client = clickhouse_connect.get_client(
    host=os.getenv("CLICKHOUSE_HOST", "localhost"),
    port=8123,
    username='default',
    password='apex_admin'
)

# Broker setup
broker = KafkaBroker(os.getenv("REDPANDA_BROKERS", "localhost:19092"))
app = FastStream(broker)

WINDOW_SIZE = 200
HALF_WINDOW = WINDOW_SIZE // 2
P_VALUE_THRESHOLD = 0.05
PSI_THRESHOLD = 0.25 

price_buffers = {
    "BTC/USD": deque(maxlen=WINDOW_SIZE),
    "ETH/USD": deque(maxlen=WINDOW_SIZE),
    "LTC/USD": deque(maxlen=WINDOW_SIZE)
}

def calculate_psi(expected, actual, buckets=10):
    def scale_by_range(data, min_val, max_val):
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
    
    # Initialize defaults to avoid NameErrors
    z_score = 0.0
    p_value = 1.0  # Default to "stable"
    psi = 0.0      # Default to "no drift"

    # 1. Z-SCORE CHECK
    if len(buffer) > 50: 
        mean, std = np.mean(buffer), np.std(buffer)
        z_score = abs(price - mean) / std if std > 0 else 0
        if z_score > 3.5:
            print(f"⚠️ DATA WARNING [{symbol}]: Outlier! Z-Score: {z_score:.2f}")

    buffer.append(price)

    # 2. DISTRIBUTION & DRIFT CHECKS
    # We only insert into ClickHouse when the window is full and we run the math
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
        else:
            print(f"📊 {symbol} Stable | PSI: {psi:.4f} | KS p-value: {p_value:.4f}")
        
        # 3. DB INSERT (Now safely inside the window check)
        try:
            ch_client.insert(
                'default.drift_metrics',
                [[symbol, float(p_value), float(psi), float(z_score), datetime.utcnow()]],
                column_names=['symbol', 'ks_p_value', 'psi_value', 'z_score', 'timestamp']
            )
        except Exception as e:
            print(f"❌ Failed to save metrics: {e}")

if __name__ == "__main__":
    print("🧠 Apex-Guardian Advanced Quant Engine live...")
    asyncio.run(app.run())
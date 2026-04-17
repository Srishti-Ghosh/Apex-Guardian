import os
from datetime import datetime
from dotenv import load_dotenv
import clickhouse_connect
from faststream import FastStream  # <-- NEW: Bringing in the core engine
from faststream.kafka import KafkaBroker

load_dotenv()

# 1. Connect to Redpanda
broker = KafkaBroker(os.getenv("REDPANDA_BROKERS", "localhost:19092"))

# 2. Initialize the FastStream App (This manages the listening loop!)
app = FastStream(broker)

# 3. Connect to ClickHouse
ch_host = os.getenv("CLICKHOUSE_HOST", "localhost")

ch_client = clickhouse_connect.get_client(
    host=ch_host, 
    port=8123, 
    username='default', 
    password='apex_admin'
)

BATCH_SIZE = 100
message_buffer = []

# Using a new group_id so it pulls all the historical messages you generated
@broker.subscriber("market-live", group_id="apex-guardian-v2", auto_offset_reset="earliest")
async def ingest_to_clickhouse(msg: dict):
    global message_buffer
    
    print(f"📥 Received from Redpanda: {msg['symbol']} at {msg['price']}")

    if "status" in msg:
        return

    try:
        row = [
            msg["symbol"],
            float(msg["price"]),
            datetime.fromisoformat(msg["timestamp"].replace('Z', '+00:00')),
            msg["source"]
        ]
        
        message_buffer.append(row)
        print(f"📈 Buffer: {len(message_buffer)}/{BATCH_SIZE}")

        if len(message_buffer) >= BATCH_SIZE:
            print("📦 Buffer full! Attempting ClickHouse insert...")
            ch_client.insert(
                'default.market_ticks', 
                message_buffer, 
                column_names=['symbol', 'price', 'timestamp', 'source']
            )
            print("✅ Batch successfully persisted.")
            message_buffer.clear()

    except Exception as e:
        print(f"🔥 ClickHouse Write Failed! Redirecting to DLQ...")
        # Send the failed batch to a Dead Letter Queue for manual recovery later
        await broker.publish(message_buffer, topic="dead-letter-queue")
        message_buffer.clear()

if __name__ == "__main__":
    import asyncio
    print("🛡️ Apex-Guardian Consumer starting up via FastStream...")
    # This replaces our manual wait loop. FastStream takes the wheel here.
    asyncio.run(app.run())
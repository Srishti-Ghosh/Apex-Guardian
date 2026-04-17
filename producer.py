import asyncio
import os
import json
from dotenv import load_dotenv
from alpaca.data.live import CryptoDataStream
from faststream.kafka import KafkaBroker

load_dotenv()

# Connect to our Redpanda broker
broker = KafkaBroker(os.getenv("REDPANDA_BROKERS"))

async def stream_market_data():
    stream_client = CryptoDataStream(
        os.getenv("ALPACA_API_KEY"), 
        os.getenv("ALPACA_SECRET_KEY")
    )

    # Change handler to handle 'quotes' instead of 'trades'
    async def quote_handler(data):
        payload = {
            "symbol": data.symbol,
            "price": (data.bid_price + data.ask_price) / 2, # Use mid-price
            "timestamp": str(data.timestamp),
            "source": "alpaca-crypto-quote"
        }
        await broker.publish(payload, topic="market-live")
        print(f"⚡ Quote Ingested: {data.symbol} | Mid: ${payload['price']}")

    # Subscribe to QUOTES instead of TRADES
    stream_client.subscribe_quotes(quote_handler, "BTC/USD", "ETH/USD", "LTC/USD")

    async with broker:
        await broker.publish({"status": "system_start"}, topic="market-live")
        print("🚀 Apex-Guardian Producer is live (High Volume Mode)...")
        await stream_client._run_forever()

if __name__ == "__main__":
    try:
        asyncio.run(stream_market_data())
    except KeyboardInterrupt:
        print("Stopping ingest...")
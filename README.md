# 🛡️ Apex-Guardian
**Distributed High-Throughput Ingest & Quant Model Surveillance Engine**

Apex-Guardian is a cloud-native, event-driven data pipeline designed to ingest, store, and statistically validate high-frequency financial market data in real-time. It acts as a bridge between low-latency infrastructure engineering and quantitative model risk management.

## 🚀 Architecture Highlights
* **Ingestion:** Asynchronous Python (FastStream/WebSockets) pulling live crypto ticks.
* **Message Broker:** Redpanda (C++ Kafka) for backpressure management and decoupled routing.
* **OLAP Storage:** ClickHouse with `ZSTD(1)` columnar compression and daily partitioning for sub-second aggregations.
* **Quantitative Engine:** Real-time stream processing calculating **Population Stability Index (PSI)** and **Kolmogorov-Smirnov (KS)** tests to detect market regime shifts and data drift.
* **Observability:** Live Grafana dashboarding tracking system throughput and statistical anomalies.

## 🛠️ Tech Stack
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Redpanda](https://img.shields.io/badge/Redpanda-000000?style=for-the-badge&logo=apachekafka&logoColor=white)
![ClickHouse](https://img.shields.io/badge/ClickHouse-FFCC01?style=for-the-badge&logo=clickhouse&logoColor=black)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![Kubernetes](https://img.shields.io/badge/Kubernetes-326CE5?style=for-the-badge&logo=kubernetes&logoColor=white)
![Grafana](https://img.shields.io/badge/Grafana-F46800?style=for-the-badge&logo=grafana&logoColor=white)

## ⚙️ Quick Start (One-Command Deploy)
Ensure you have Docker and Docker Compose installed.

1. Clone the repository:
   ```bash
   git clone [https://github.com/YOUR_USERNAME/Apex-Guardian.git](https://github.com/YOUR_USERNAME/Apex-Guardian.git)
   cd Apex-Guardian
# Apex-Guardian Automated Pipeline

.PHONY: up down clean logs restart

up:
	@echo "🚀 Starting Apex-Guardian Infrastructure..."
	docker-compose up -d --build
	@echo "✅ System is live. Grafana available at http://localhost:3000"

down:
	@echo "🛑 Stopping Apex-Guardian Infrastructure..."
	docker-compose down
	@echo "✅ System offline."

clean:
	@echo "🧹 Wiping all volumes and data..."
	docker-compose down -v
	@echo "✅ Clean slate achieved."

logs:
	docker-compose logs -f

restart: down up
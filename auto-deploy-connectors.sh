#!/bin/bash
# Auto Deploy MM2 Connectors Script
# Bu script MM2 Container'ın içinde çalışır ve connector'ları otomatik deploy eder

echo "🔄 Auto Connector Deployment başlatılıyor..."
sleep 30  # Connect cluster'ın tamamen hazır olması için bekle

# Connect cluster'ın hazır olup olmadığını kontrol et
for i in {1..20}; do
    if curl -s http://localhost:8083/ > /dev/null; then
        echo "✅ Connect cluster hazır!"
        break
    fi
    echo "⏳ Connect cluster bekleniyor... ($i/20)"
    sleep 10
done

# Connector'ları deploy et
echo "🚀 Connector'lar deploy ediliyor..."

# Source Connector
echo "📤 Source Connector deploy ediliyor..."
curl -X POST http://localhost:8083/connectors \
     -H "Content-Type: application/json" \
     -d @/etc/kafka/connect/mm2-source-connector.json

echo ""

# Heartbeat Connector  
echo "💓 Heartbeat Connector deploy ediliyor..."
curl -X POST http://localhost:8083/connectors \
     -H "Content-Type: application/json" \
     -d @/etc/kafka/connect/mm2-heartbeat-connector.json

echo ""

# Checkpoint Connector
echo "📋 Checkpoint Connector deploy ediliyor..."
curl -X POST http://localhost:8083/connectors \
     -H "Content-Type: application/json" \
     -d @/etc/kafka/connect/mm2-checkpoint-connector.json

echo ""
echo "✅ Auto deployment tamamlandı!"

# Status kontrolü
sleep 5
echo "📊 Connector durumları:"
curl -s http://localhost:8083/connectors | jq '.'

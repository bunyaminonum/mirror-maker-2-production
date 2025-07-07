#!/bin/bash
# Auto Deploy MM2 Connectors Script
# This script runs inside MM2 Container and automatically deploys connectors

echo "🔄 Starting Auto Connector Deployment..."
sleep 30  # Wait for Connect cluster to be fully ready

# Check if Connect cluster is ready
for i in {1..20}; do
    if curl -s http://localhost:8083/ > /dev/null; then
        echo "✅ Connect cluster ready!"
        break
    fi
    echo "⏳ Waiting for Connect cluster... ($i/20)"
    sleep 10
done

# Deploy connectors
echo "🚀 Deploying connectors..."

# Source Connector
echo "📤 Deploying Source Connector..."
curl -X POST http://localhost:8083/connectors \
     -H "Content-Type: application/json" \
     -d @/etc/kafka/connect/mm2-source-connector.json

echo ""

# Heartbeat Connector  
echo "💓 Deploying Heartbeat Connector..."
curl -X POST http://localhost:8083/connectors \
     -H "Content-Type: application/json" \
     -d @/etc/kafka/connect/mm2-heartbeat-connector.json

echo ""

# Checkpoint Connector
echo "📋 Deploying Checkpoint Connector..."
curl -X POST http://localhost:8083/connectors \
     -H "Content-Type: application/json" \
     -d @/etc/kafka/connect/mm2-checkpoint-connector.json

echo ""
echo "✅ Auto deployment completed!"

# Status check
sleep 5
echo "📊 Connector statuses:"
curl -s http://localhost:8083/connectors

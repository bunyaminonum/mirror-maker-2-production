# Confluent Kafka 7.9 Mirror Maker 2 Production Setup

Production-ready MirrorMaker 2 setup with distributed Kafka Connect, auto-deployment, and comprehensive testing scripts for disaster recovery scenarios.

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  Source         │    │   Mirror Maker 2 │    │  Target         │
│  Cluster        │───▶│                  │───▶│  Cluster        │
│  (kafka:9092)   │    │   Replication    │    │ (kafka:9093)    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### Components
- **Source Cluster**: Zookeeper-1 + Kafka-Source (Port: 9092)
- **Target Cluster**: Zookeeper-2 + Kafka-Target (Port: 9093)
- **Mirror Maker 2**: Continuous replication from Source to Target
- **Distributed Connect**: Production-ready Kafka Connect cluster
- **Python Producer**: Sends messages to source cluster
- **Python Consumers**: Reads messages from both clusters

## 🚀 Quick Start

### 1. Prerequisites
- Docker & Docker Compose
- Python 3.7+
- pip

### 2. Install Python Packages
```powershell
pip install -r requirements.txt
```

### 3. Start the Entire System
```powershell
docker-compose up -d
```

### 4. Check System Status
```powershell
docker-compose ps
```

### 5. Verify System Health
```powershell
# Check source cluster topics
docker exec kafka-source kafka-topics --bootstrap-server localhost:9092 --list

# Check target cluster topics  
docker exec kafka-target kafka-topics --bootstrap-server localhost:9093 --list
```

## 📊 Test Scenarios

### Scenario 1: Normal Operation Test

1. **Start Producer** (New terminal):

```powershell
python producer_orders.py
```

2. **Start Source Consumer** (New terminal):

```powershell
python consumer_orders.py
```

3. **Start DR Consumer** (New terminal):

```powershell
python consumer_dr_orders.py
```

### Scenario 2: Disaster Recovery Test

1. **Run Management Tool**:

```powershell
python mm2_manager.py status
```

2. **Test End-to-End Replication**:
   - Producer sends messages to source cluster
   - MirrorMaker 2 replicates to target cluster
   - DR consumer reads from mirrored topics
   - Verify offset synchronization

### Scenario 3: Manual Disaster Recovery

1. **Stop Source Cluster**:

```powershell
docker stop kafka-source zookeeper-1
```

2. **Continue with DR Consumer**:

```powershell
python consumer_dr_orders.py
```

3. **Restart Source Cluster**:

```powershell
docker start zookeeper-1 kafka-source
```
```powershell
## 🖥️ Monitoring

### REST API
- **URL**: <http://localhost:8083>
- **Connectors**: GET /connectors
- **Status**: GET /connectors/{name}/status

### Command Line Tools

**List Topics**:

```powershell
# Source cluster
docker exec kafka-source kafka-topics --bootstrap-server localhost:9092 --list

# Target cluster
docker exec kafka-target kafka-topics --bootstrap-server localhost:9093 --list
```

**Check Consumer Groups**:

```powershell
# Source cluster
docker exec kafka-source kafka-consumer-groups --bootstrap-server localhost:9092 --list

# Target cluster
docker exec kafka-target kafka-consumer-groups --bootstrap-server localhost:9093 --list
```

**Monitor Mirror Maker 2 Logs**:

```powershell
docker logs mirror-maker-2 -f
```

### Python Management Tool

```powershell
# Check all connector status
python mm2_manager.py status

# Deploy all connectors
python mm2_manager.py deploy

# Delete all connectors
python mm2_manager.py delete-all
```

## 📁 Project Structure

```text
mirror-maker-2-production/
├── docker-compose.yml           # Main Docker Compose file
├── requirements.txt             # Python dependencies
├── producer_orders.py           # Source cluster producer
├── consumer_orders.py           # Source cluster consumer  
├── consumer_dr_orders.py        # Target cluster consumer
├── mm2_manager.py               # Connector management tool
├── README.md                    # This file
├── connect/
│   ├── connect-distributed.properties  # Kafka Connect config
│   ├── connect-log4j.properties       # Logging configuration
│   ├── mm2-source-connector.json      # Source connector config
│   ├── mm2-heartbeat-connector.json   # Heartbeat connector config
│   ├── mm2-checkpoint-connector.json  # Checkpoint connector config
│   └── auto-deploy-connectors.sh      # Auto-deployment script
└── mirror-maker-config/
    └── mm2.properties              # Legacy MM2 configuration
```

## 🔧 Configuration Details

### Mirror Maker 2 Settings

- **Source**: Source cluster (kafka-source:29092)
- **Target**: Target cluster (kafka-target:29093)
- **Topics**: `orders`
- **Consumer Groups**: `order-processing-group`
- **Replication Policy**: DefaultReplicationPolicy

### Topic Naming Convention

- Source cluster: `orders`
- Target cluster: `source.orders` (MirrorMaker 2 adds prefix)

## 🚨 Troubleshooting

### Common Issues

1. **Containers won't start**:

```powershell
docker-compose down
docker-compose up -d
```

2. **Topics not visible**:

```powershell
# Wait 30 seconds, then check again
docker exec kafka-source kafka-topics --bootstrap-server localhost:9092 --list
```

3. **Mirror Maker 2 not working**:

```powershell
docker logs mirror-maker-2
```

4. **Python import errors**:

```powershell
pip install kafka-python confluent-kafka python-snappy
```

### Port Reference

- **9092**: Source Kafka
- **9093**: Target Kafka
- **2181**: Source Zookeeper
- **2182**: Target Zookeeper  
- **8083**: Kafka Connect REST API

## 📈 Advanced Testing

### Offset Synchronization

```powershell
# Check consumer offsets
docker exec kafka-source kafka-consumer-groups --bootstrap-server localhost:9092 --group order-processing-group --describe

docker exec kafka-target kafka-consumer-groups --bootstrap-server localhost:9093 --group order-processing-group --describe
```

### Performance Testing

```powershell
# High throughput producer test
docker exec kafka-source kafka-producer-perf-test --topic orders --num-records 10000 --record-size 1024 --throughput 1000 --producer-props bootstrap.servers=localhost:9092
```

### Connector Management

```powershell
# Check connector status
python mm2_manager.py status

# Restart failed connectors
python mm2_manager.py deploy
```

## 🧹 Cleanup

Clean all containers and volumes:

```powershell
docker-compose down -v
docker system prune -f
```

## 📚 Notes

- This is a production-ready setup with self-healing capabilities
- MirrorMaker 2 synchronizes both topics and consumer group offsets
- In DR scenarios, consumers can seamlessly continue reading from the target cluster
- All internal topics use `cleanup.policy=compact` for optimal performance
- Connectors auto-deploy on system startup for zero-config operation
- REST API allows for dynamic connector management and monitoring

## 🎯 Production Features

- **Distributed Mode**: Scalable Kafka Connect cluster
- **Auto-Deployment**: Connectors deploy automatically on startup
- **Self-Healing**: Topics and configurations auto-created with correct settings
- **Monitoring**: REST API and Python management tools
- **Zero Downtime**: Hot-swappable connector configurations
- **Offset Sync**: Consumer group offsets replicated for seamless failover

## 📞 Support

For issues and contributions, please use the GitHub repository:
<https://github.com/bunyaminonum/mirror-maker-2-production>

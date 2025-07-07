# Confluent 7.9 MM2 Active-Passive Kurulum Rehberi

## Ön Gereksinimler ve Planlama

### Cluster Yapısı
- **Primary Cluster (Active)**: Üretim ortamı
- **Secondary Cluster (Passive)**: DR ortamı
- **MM2 Cluster**: Replication işlemlerini yönetir

### Gerekli Bileşenler
- Confluent Platform 7.9
- Kafka Connect (MM2 için)
- Schema Registry (varsa)
- Control Center (opsiyonel)

## 1. Ağ ve Güvenlik Yapılandırması

### Cluster Arası Bağlantı
```bash
# Primary cluster'dan secondary cluster'a erişim testi
kafka-topics --bootstrap-server secondary-cluster:9092 --list

# Secondary cluster'dan primary cluster'a erişim testi
kafka-topics --bootstrap-server primary-cluster:9092 --list
```

### Güvenlik Yapılandırması (SASL/SSL)
```properties
# security.properties
security.protocol=SASL_SSL
sasl.mechanism=PLAIN
sasl.jaas.config=org.apache.kafka.common.security.plain.PlainLoginModule required \
    username="mm2-user" \
    password="mm2-password";
ssl.truststore.location=/path/to/truststore.jks
ssl.truststore.password=truststore-password
```

## 2. MM2 Yapılandırma Dosyaları

### Ana MM2 Konfigürasyonu
```properties
# mm2.properties
# Cluster tanımları
clusters = primary, secondary
primary.bootstrap.servers = primary-broker1:9092,primary-broker2:9092,primary-broker3:9092
secondary.bootstrap.servers = secondary-broker1:9092,secondary-broker2:9092,secondary-broker3:9092

# Replication flow (sadece primary -> secondary)
primary->secondary.enabled = true
secondary->primary.enabled = false

# Topic naming ve mapping
replication.factor = 3
primary->secondary.topics = .*
primary->secondary.topics.blacklist = __.*,.*-internal,connect-.*

# Consumer group replication
primary->secondary.sync.group.offsets.enabled = true
primary->secondary.sync.group.offsets.interval.seconds = 60
primary->secondary.emit.checkpoints.enabled = true
primary->secondary.emit.checkpoints.interval.seconds = 60

# Heartbeat topic
primary->secondary.emit.heartbeats.enabled = true
primary->secondary.emit.heartbeats.interval.seconds = 5

# Topic configuration sync
primary->secondary.sync.topic.configs.enabled = true
primary->secondary.sync.topic.acls.enabled = true
```

### MM2 Source Connector Konfigürasyonu
```properties
# mm2-source.properties
name=mm2-source-connector
connector.class=org.apache.kafka.connect.mirror.MirrorSourceConnector
source.cluster.alias=primary
target.cluster.alias=secondary

# Cluster bağlantı bilgileri
source.cluster.bootstrap.servers=primary-broker1:9092,primary-broker2:9092,primary-broker3:9092
target.cluster.bootstrap.servers=secondary-broker1:9092,secondary-broker2:9092,secondary-broker3:9092

# Topic seçimi
topics=.*
topics.blacklist=__.*,.*-internal,connect-.*,_confluent.*

# Performans ayarları
tasks.max=4
refresh.topics.enabled=true
refresh.topics.interval.seconds=300
sync.topic.configs.enabled=true
sync.topic.acls.enabled=true

# Offset translation
offset-syncs.topic.replication.factor=3
offset-syncs.topic.retention.ms=604800000
```

### MM2 Checkpoint Connector Konfigürasyonu
```properties
# mm2-checkpoint.properties
name=mm2-checkpoint-connector
connector.class=org.apache.kafka.connect.mirror.MirrorCheckpointConnector
source.cluster.alias=primary
target.cluster.alias=secondary

# Cluster bağlantı bilgileri
source.cluster.bootstrap.servers=primary-broker1:9092,primary-broker2:9092,primary-broker3:9092
target.cluster.bootstrap.servers=secondary-broker1:9092,secondary-broker2:9092,secondary-broker3:9092

# Consumer group sync - TÜM CONSUMER GROUP'LARI SYNC EDER
groups=.*
groups.blacklist=__.*,connect-.*,_confluent.*,console-consumer-.*
sync.group.offsets.enabled=true
sync.group.offsets.interval.seconds=60
emit.checkpoints.enabled=true
emit.checkpoints.interval.seconds=60

# Checkpoint topic - Consumer offset'leri saklar
checkpoints.topic.replication.factor=3
checkpoints.topic.retention.ms=604800000
checkpoints.topic.cleanup.policy=compact

# Offset translation için gerekli
offset.syncs.topic.replication.factor=3
refresh.groups.enabled=true
refresh.groups.interval.seconds=300
```

### MM2 Heartbeat Connector Konfigürasyonu
```properties
# mm2-heartbeat.properties
name=mm2-heartbeat-connector
connector.class=org.apache.kafka.connect.mirror.MirrorHeartbeatConnector
source.cluster.alias=primary
target.cluster.alias=secondary

# Cluster bağlantı bilgileri
source.cluster.bootstrap.servers=primary-broker1:9092,primary-broker2:9092,primary-broker3:9092
target.cluster.bootstrap.servers=secondary-broker1:9092,secondary-broker2:9092,secondary-broker3:9092

# Heartbeat ayarları
emit.heartbeats.enabled=true
emit.heartbeats.interval.seconds=5
heartbeats.topic.replication.factor=3
heartbeats.topic.retention.ms=604800000
```

## 3. Kafka Connect Cluster Kurulumu

### Connect Worker Konfigürasyonu
```properties
# connect-distributed.properties
bootstrap.servers=primary-broker1:9092,primary-broker2:9092,primary-broker3:9092
group.id=mm2-connect-cluster

# Offset, config ve status topics
offset.storage.topic=mm2-connect-offsets
offset.storage.replication.factor=3
offset.storage.partitions=25

config.storage.topic=mm2-connect-configs
config.storage.replication.factor=3

status.storage.topic=mm2-connect-status
status.storage.replication.factor=3
status.storage.partitions=5

# Converter ayarları
key.converter=org.apache.kafka.connect.json.JsonConverter
value.converter=org.apache.kafka.connect.json.JsonConverter
key.converter.schemas.enable=false
value.converter.schemas.enable=false

# Plugin path
plugin.path=/usr/share/confluent-hub-components,/usr/share/java

# Rest interface
rest.port=8083
rest.advertised.host.name=connect-worker-1
rest.advertised.port=8083
```

## 4. Kurulum Adımları

### Adım 1: Connect Cluster Başlatma
```bash
# Connect worker'ları başlat
systemctl start confluent-kafka-connect

# Connect cluster durumunu kontrol et
curl -X GET http://connect-worker-1:8083/
curl -X GET http://connect-worker-1:8083/connectors
```

### Adım 2: MM2 Connector'ları Kurma
```bash
# Source connector kurulumu
curl -X POST http://connect-worker-1:8083/connectors \
  -H "Content-Type: application/json" \
  -d @mm2-source.json

# Checkpoint connector kurulumu
curl -X POST http://connect-worker-1:8083/connectors \
  -H "Content-Type: application/json" \
  -d @mm2-checkpoint.json

# Heartbeat connector kurulumu
curl -X POST http://connect-worker-1:8083/connectors \
  -H "Content-Type: application/json" \
  -d @mm2-heartbeat.json
```

### Adım 3: JSON Konfigürasyon Dosyaları
```json
// mm2-source.json
{
  "name": "mm2-source-connector",
  "config": {
    "connector.class": "org.apache.kafka.connect.mirror.MirrorSourceConnector",
    "source.cluster.alias": "primary",
    "target.cluster.alias": "secondary",
    "source.cluster.bootstrap.servers": "primary-broker1:9092,primary-broker2:9092,primary-broker3:9092",
    "target.cluster.bootstrap.servers": "secondary-broker1:9092,secondary-broker2:9092,secondary-broker3:9092",
    "topics": ".*",
    "topics.blacklist": "__.*,.*-internal,connect-.*,_confluent.*",
    "tasks.max": "4",
    "refresh.topics.enabled": "true",
    "refresh.topics.interval.seconds": "300",
    "sync.topic.configs.enabled": "true",
    "offset-syncs.topic.replication.factor": "3"
  }
}
```

## 5. Monitoring ve Doğrulama

### Replication Lag Monitoring
```bash
# Heartbeat topic'i kontrol et
kafka-console-consumer --bootstrap-server secondary-broker1:9092 \
  --topic heartbeats \
  --from-beginning

# Offset sync durumu
kafka-console-consumer --bootstrap-server secondary-broker1:9092 \
  --topic primary.offset-syncs.internal \
  --from-beginning
```

### JMX Metrics
```bash
# Replication lag
kafka.connect.mirror:type=MirrorSourceConnector,source=primary,target=secondary,topic=*,partition=*

# Checkpoint lag
kafka.connect.mirror:type=MirrorCheckpointConnector,source=primary,target=secondary
```

### Grafana Dashboard Query'leri
```promql
# Replication lag
kafka_connect_mirror_source_connector_replication_lag_ms

# Checkpoint lag
kafka_connect_mirror_checkpoint_connector_lag_ms

# Heartbeat freshness
kafka_connect_mirror_heartbeat_connector_freshness_ms
```

## 6. Failover Prosedürü

### Planned Failover
```bash
# 1. Primary cluster'ı graceful shutdown
systemctl stop confluent-kafka

# 2. Son checkpoint'leri bekle
sleep 60

# 3. Secondary cluster'da consumer group offset'lerini restore et
kafka-console-consumer --bootstrap-server secondary-broker1:9092 \
  --topic primary.checkpoints.internal \
  --from-beginning

# 4. Application'ları secondary cluster'a yönlendir
# DNS değişikliği veya load balancer konfigürasyonu
```

### Unplanned Failover
```bash
# 1. Primary cluster durumunu kontrol et
kafka-topics --bootstrap-server primary-broker1:9092 --list

# 2. Secondary cluster'da son durum
kafka-topics --bootstrap-server secondary-broker1:9092 --list

# 3. Consumer group'ları secondary cluster'a taşı
kafka-consumer-groups --bootstrap-server secondary-broker1:9092 --list

# 4. Application connection string'leri değiştir
```

## 7. Failback Prosedürü

### Primary Cluster Hazırlama
```bash
# 1. Primary cluster'ı temizle
kafka-topics --bootstrap-server primary-broker1:9092 --delete --topic '.*'

# 2. Reverse replication başlat
# MM2 konfigürasyonunu tersine çevir
secondary->primary.enabled = true
primary->secondary.enabled = false

# 3. Data sync tamamlandıktan sonra switch back
```

## 11. Consumer Offset Yönetimi Detayları

### MM2 Consumer Offset Nasıl Çalışır?

MM2 üç ana bileşenle consumer offset'leri yönetir:

1. **MirrorSourceConnector**: Topic'leri ve mesajları replicate eder
2. **MirrorCheckpointConnector**: Consumer group offset'lerini sync eder
3. **Offset Translation**: Primary cluster offset'lerini secondary cluster offset'lerine çevirir

### Offset Sync Mekanizması
```bash
# Primary cluster'daki consumer group'ları kontrol et
kafka-consumer-groups --bootstrap-server primary-broker1:9092 --list

# Secondary cluster'da sync edilen group'ları kontrol et
kafka-consumer-groups --bootstrap-server secondary-broker1:9092 --list

# Checkpoint topic'ini incele
kafka-console-consumer --bootstrap-server secondary-broker1:9092 \
  --topic primary.checkpoints.internal \
  --from-beginning \
  --property print.key=true
```

### Offset Translation Tablosu
```bash
# Offset sync topic'ini kontrol et
kafka-console-consumer --bootstrap-server secondary-broker1:9092 \
  --topic primary.offset-syncs.internal \
  --from-beginning \
  --property print.key=true

# Bu topic şu bilgileri içerir:
# - Primary cluster partition offset'i
# - Secondary cluster karşılık gelen offset'i
# - Translation timestamp
```

### Consumer Group Failover Örneği
```bash
# 1. Primary cluster'da consumer group durumu
kafka-consumer-groups --bootstrap-server primary-broker1:9092 \
  --group my-app-group --describe

# Output:
# TOPIC     PARTITION  CURRENT-OFFSET  LOG-END-OFFSET  LAG
# orders    0          1000            1000            0
# orders    1          1500            1500            0

# 2. Secondary cluster'da replicated topic durumu
kafka-consumer-groups --bootstrap-server secondary-broker1:9092 \
  --group my-app-group --describe

# Output:
# TOPIC           PARTITION  CURRENT-OFFSET  LOG-END-OFFSET  LAG
# primary.orders  0          950             980             30
# primary.orders  1          1450            1480            30
```

### Failover Sırasında Offset Restore
```bash
# 1. Consumer group'u reset et (gerekirse)
kafka-consumer-groups --bootstrap-server secondary-broker1:9092 \
  --group my-app-group --reset-offsets \
  --to-current --topic primary.orders --execute

# 2. Checkpoint'lerden offset'leri restore et
kafka-console-consumer --bootstrap-server secondary-broker1:9092 \
  --topic primary.checkpoints.internal \
  --from-beginning \
  --property print.key=true \
  --property print.timestamp=true | \
  grep "my-app-group"

# 3. Manual offset commit (gerekirse)
kafka-consumer-groups --bootstrap-server secondary-broker1:9092 \
  --group my-app-group --reset-offsets \
  --to-offset 950 --topic primary.orders:0 --execute
```

### Offset Monitoring ve Alerting
```bash
# Checkpoint freshness kontrol
kafka-run-class kafka.tools.ConsumerLagChecker \
  --bootstrap-server secondary-broker1:9092 \
  --group my-app-group

# Offset sync lag hesaplama
#!/bin/bash
PRIMARY_OFFSET=$(kafka-run-class kafka.tools.GetOffsetShell \
  --broker-list primary-broker1:9092 \
  --topic orders --time -1 | cut -d: -f3)

SECONDARY_OFFSET=$(kafka-run-class kafka.tools.GetOffsetShell \
  --broker-list secondary-broker1:9092 \
  --topic primary.orders --time -1 | cut -d: -f3)

echo "Replication lag: $((PRIMARY_OFFSET - SECONDARY_OFFSET))"
```

### Consumer Group Yönetimi Best Practices
```properties
# MM2 Checkpoint Connector - Gelişmiş Ayarlar
name=mm2-checkpoint-connector
connector.class=org.apache.kafka.connect.mirror.MirrorCheckpointConnector

# Spesifik consumer group'ları sync et
groups=payment-service,order-service,inventory-service
groups.blacklist=test-.*,debug-.*,console-consumer-.*

# Checkpoint frequency - Daha sık sync için
emit.checkpoints.interval.seconds=30
sync.group.offsets.interval.seconds=30

# Checkpoint retention - Daha uzun süre sakla
checkpoints.topic.retention.ms=2592000000  # 30 gün
checkpoints.topic.segment.ms=86400000      # 1 gün

# Group discovery - Yeni group'ları otomatik keşfet
refresh.groups.enabled=true
refresh.groups.interval.seconds=60
```

### Otomatik Failover Script
```bash
#!/bin/bash
# auto-failover-consumer-groups.sh

SECONDARY_BOOTSTRAP="secondary-broker1:9092"
PRIMARY_BOOTSTRAP="primary-broker1:9092"

# Primary cluster durumunu kontrol et
if ! kafka-topics --bootstrap-server $PRIMARY_BOOTSTRAP --list &>/dev/null; then
    echo "Primary cluster unreachable, initiating failover..."
    
    # Tüm consumer group'ları listele
    GROUPS=$(kafka-consumer-groups --bootstrap-server $SECONDARY_BOOTSTRAP --list | grep -v "^$")
    
    for GROUP in $GROUPS; do
        echo "Processing group: $GROUP"
        
        # Checkpoint'lerden en son offset'leri al
        LAST_CHECKPOINT=$(kafka-console-consumer \
            --bootstrap-server $SECONDARY_BOOTSTRAP \
            --topic primary.checkpoints.internal \
            --from-beginning --max-messages 1000 \
            --property print.key=true \
            --timeout-ms 10000 | \
            grep "$GROUP" | tail -1)
        
        if [ ! -z "$LAST_CHECKPOINT" ]; then
            echo "Found checkpoint for $GROUP: $LAST_CHECKPOINT"
            # Burada offset'leri parse edip consumer group'a commit edebilirsiniz
        fi
    done
fi
```

## 8. Sorun Giderme
```bash
# 1. Checkpoint connector durumu
curl -X GET http://connect-worker-1:8083/connectors/mm2-checkpoint-connector/status

# 2. Checkpoint topic'inde veri var mı?
kafka-console-consumer --bootstrap-server secondary-broker1:9092 \
  --topic primary.checkpoints.internal \
  --from-beginning --max-messages 10

# 3. Offset sync topic'inde veri var mı?
kafka-console-consumer --bootstrap-server secondary-broker1:9092 \
  --topic primary.offset-syncs.internal \
  --from-beginning --max-messages 10

# 4. Consumer group'lar sync ediliyor mu?
kafka-consumer-groups --bootstrap-server secondary-broker1:9092 \
  --list | grep -v "^$"

# 5. Specific group offset durumu
kafka-consumer-groups --bootstrap-server secondary-broker1:9092 \
  --group my-app-group --describe
```

### Yaygın Sorunlar
```bash
# Connector durumu kontrol
curl -X GET http://connect-worker-1:8083/connectors/mm2-source-connector/status

# Log kontrolü
tail -f /var/log/confluent/kafka-connect/kafka-connect.log

# Topic missing hatası
kafka-topics --bootstrap-server secondary-broker1:9092 \
  --create --topic primary.heartbeats \
  --partitions 1 --replication-factor 3
```

### Performance Tuning
```properties
# Connector seviyesinde
tasks.max=8
refresh.topics.enabled=true
refresh.topics.interval.seconds=60

# Consumer seviyesinde
consumer.max.poll.records=10000
consumer.fetch.min.bytes=1024
consumer.fetch.max.wait.ms=500

# Producer seviyesinde
producer.batch.size=65536
producer.linger.ms=5
producer.compression.type=snappy
```

## 9. Operasyonel Görevler

### Günlük Kontroller
```bash
#!/bin/bash
# daily-mm2-check.sh

echo "=== MM2 Connector Status ==="
curl -s http://connect-worker-1:8083/connectors/mm2-source-connector/status | jq

echo "=== Replication Lag ==="
kafka-run-class kafka.tools.ConsumerLagChecker \
  --bootstrap-server secondary-broker1:9092 \
  --group primary

echo "=== Heartbeat Status ==="
kafka-console-consumer --bootstrap-server secondary-broker1:9092 \
  --topic heartbeats --max-messages 1 --timeout-ms 5000
```

### Alerting Rules
```yaml
# Prometheus alerting rules
groups:
  - name: mm2-alerts
    rules:
      - alert: MM2ReplicationLag
        expr: kafka_connect_mirror_source_connector_replication_lag_ms > 30000
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "MM2 replication lag is high"
          
      - alert: MM2ConnectorDown
        expr: kafka_connect_connector_status != 1
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "MM2 connector is down"
```

## 10. Güvenlik Sertleştirme

### ACL Konfigürasyonu
```bash
# MM2 user için gerekli ACL'ler
kafka-acls --bootstrap-server primary-broker1:9092 \
  --add --allow-principal User:mm2-user \
  --operation Read --operation Write \
  --topic '*'

kafka-acls --bootstrap-server secondary-broker1:9092 \
  --add --allow-principal User:mm2-user \
  --operation Read --operation Write \
  --topic '*'
```

### SSL/TLS Konfigürasyonu
```properties
# Connect worker için SSL
security.protocol=SSL
ssl.keystore.location=/path/to/keystore.jks
ssl.keystore.password=keystore-password
ssl.key.password=key-password
ssl.truststore.location=/path/to/truststore.jks
ssl.truststore.password=truststore-password
```

Bu rehber, Confluent 7.9 üzerinde MM2 tabanlı Active-Passive replication kurulumunu kapsamaktadır. Üretim ortamında kullanmadan önce test ortamında detaylı testler yapmanız önerilir.
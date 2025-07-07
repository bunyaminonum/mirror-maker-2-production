# Confluent Kafka 7.9 Mirror Maker 2 Disaster Recovery POC

Bu proje, Confluent Kafka 7.9 kullanarak iki cluster arası Mirror Maker 2 ile disaster recovery senaryosunu test etmek için oluşturulmuştur.

## 🏗️ Mimari

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  Primary        │    │   Mirror Maker 2 │    │  DR Cluster     │
│  Cluster        │───▶│                  │───▶│                 │
│  (kafka-1:9092) │    │   Replication    │    │ (kafka-2:9093)  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### Bileşenler
- **Primary Cluster**: Zookeeper-1 + Kafka-1 (Port: 9092)
- **DR Cluster**: Zookeeper-2 + Kafka-2 (Port: 9093)
- **Mirror Maker 2**: Primary'den DR'ye sürekli replikasyon
- **Kafka UI**: Web arayüzü (Port: 8080)
- **Python Producer**: Primary cluster'a mesaj gönderir
- **Python Consumers**: Her iki cluster'dan mesaj okur

## 🚀 Hızlı Başlangıç

### 1. Gereksinimler
- Docker & Docker Compose
- Python 3.7+
- pip

### 2. Python Paketlerini Yükle
```powershell
pip install -r requirements.txt
```

### 3. Tüm Sistemi Başlat
```powershell
docker-compose up -d
```

### 4. Sistem Durumunu Kontrol Et
```powershell
docker-compose ps
```

### 5. Test Topic'i Oluştur
```powershell
# Primary cluster'da topic oluştur
docker exec kafka-1 kafka-topics --bootstrap-server localhost:9092 --topic test-topic --create --partitions 3 --replication-factor 1
```

## 📊 Test Senaryoları

### Senaryo 1: Normal Operasyon Testi

1. **Producer'ı Başlat** (Yeni terminal):
```powershell
python producer_primary.py
```

2. **Primary Consumer'ı Başlat** (Yeni terminal):
```powershell
python consumer_primary.py
```

3. **DR Consumer'ı Başlat** (Yeni terminal):
```powershell
python consumer_dr.py
```

### Senaryo 2: Disaster Recovery Testi

1. **Test Tool'unu Çalıştır**:
```powershell
python test_scenarios.py
```

2. Menüden "4. Disaster Recovery testi yap" seçin

3. Test adımları:
   - Primary cluster durdurulur
   - DR cluster'dan mesaj okunur
   - Primary cluster tekrar başlatılır
   - Offset senkronizasyonu kontrol edilir

### Senaryo 3: Manuel Disaster Recovery

1. **Primary Cluster'ı Durdur**:
```powershell
docker stop kafka-1 zookeeper-1
```

2. **DR Consumer ile Devam Et**:
```powershell
python consumer_dr.py
```

3. **Primary'yi Tekrar Başlat**:
```powershell
docker start zookeeper-1 kafka-1
```

## 🖥️ Monitoring

### Kafka UI
- URL: http://localhost:8080
- Primary Cluster: `primary-cluster`
- DR Cluster: `dr-cluster`

### Komut Satırı Kontrolleri

**Topic'leri Listele**:
```powershell
# Primary
docker exec kafka-1 kafka-topics --bootstrap-server localhost:9092 --list

# DR
docker exec kafka-2 kafka-topics --bootstrap-server localhost:9093 --list
```

**Consumer Group'ları Kontrol Et**:
```powershell
# Primary
docker exec kafka-1 kafka-consumer-groups --bootstrap-server localhost:9092 --list

# DR  
docker exec kafka-2 kafka-consumer-groups --bootstrap-server localhost:9093 --list
```

**Mirror Maker 2 Log'larını İncele**:
```powershell
docker logs mirror-maker-2 -f
```

## 📁 Dosya Yapısı

```
mirror_maker_2_POC/
├── docker-compose.yml           # Ana Docker Compose dosyası
├── requirements.txt             # Python paketleri
├── producer_primary.py          # Primary cluster producer
├── consumer_primary.py          # Primary cluster consumer
├── consumer_dr.py               # DR cluster consumer
├── test_scenarios.py            # Test senaryoları
├── README.md                    # Bu dosya
└── mirror-maker-config/
    └── mm2.properties           # Mirror Maker 2 konfigürasyonu
```

## 🔧 Konfigürasyon Detayları

### Mirror Maker 2 Ayarları
- **Source**: Primary cluster (kafka-1:29092)
- **Target**: DR cluster (kafka-2:29093)  
- **Topics**: `test-topic`
- **Consumer Groups**: `test-consumer-group`
- **Replication Policy**: DefaultReplicationPolicy

### Topic Adlandırma
- Primary'de: `test-topic`
- DR'de: `primary.test-topic` (Mirror Maker 2 prefix ekler)

## 🚨 Troubleshooting

### Yaygın Problemler

1. **Container'lar ayağa kalkmıyor**:
```powershell
docker-compose down
docker-compose up -d
```

2. **Topic'ler görünmüyor**:
```powershell
# 30 saniye bekleyin, sonra tekrar kontrol edin
docker exec kafka-1 kafka-topics --bootstrap-server localhost:9092 --list
```

3. **Mirror Maker 2 çalışmıyor**:
```powershell
docker logs mirror-maker-2
```

4. **Python import hatası**:
```powershell
pip install kafka-python confluent-kafka
```

### Port Kontrolleri
- 9092: Primary Kafka
- 9093: DR Kafka  
- 2181: Primary Zookeeper
- 2182: DR Zookeeper
- 8080: Kafka UI

## 📈 İleri Seviye Testler

### Offset Senkronizasyonu
```powershell
# Consumer offset'lerini kontrol et
docker exec kafka-1 kafka-consumer-groups --bootstrap-server localhost:9092 --group test-consumer-group --describe

docker exec kafka-2 kafka-consumer-groups --bootstrap-server localhost:9093 --group test-consumer-group --describe
```

### Performans Testi
```powershell
# Yüksek throughput producer testi
docker exec kafka-1 kafka-producer-perf-test --topic test-topic --num-records 10000 --record-size 1024 --throughput 1000 --producer-props bootstrap.servers=localhost:9092
```

## 🧹 Temizlik

Tüm container'ları ve volume'ları temizle:
```powershell
docker-compose down -v
docker system prune -f
```

## 📚 Notlar

- Bu POC sadece test amaçlıdır, production kullanımı için ek güvenlik ve performans optimizasyonları gereklidir
- Mirror Maker 2, topic'lerin yanı sıra consumer group offset'lerini de senkronize eder
- DR senaryosunda consumer'lar kesintisiz olarak DR cluster'dan okumaya devam edebilir
- Kafka UI ile real-time olarak mesaj akışını izleyebilirsiniz

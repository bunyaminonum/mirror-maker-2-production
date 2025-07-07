#!/usr/bin/env python3
"""
Siparisler topic'ini dinleyen Consumer
Dokümandaki test senaryosuna uygun
"""

from kafka import KafkaConsumer
import json
import time
import sys

def main():
    # Aktif cluster bilgisini manuel olarak belirtiyoruz (basit test için)
    # Gerçek uygulamada bu Consul'dan okunacak
    
    CLUSTER_CONFIG = {
        'kaynak': 'localhost:9092',
        'hedef': 'localhost:9093'
    }
    
    # Şimdilik kaynak cluster'ı kullanıyoruz
    active_cluster = 'kaynak'
    bootstrap_servers = CLUSTER_CONFIG[active_cluster]
    
    print(f"Aktif küme: {active_cluster}")
    print(f"Bootstrap servers: {bootstrap_servers}")
    print("Dinlenen Konu: siparisler")
    print("Consumer Group: siparis-isleme-grubu")
    print("-" * 50)
    
    try:
        consumer = KafkaConsumer(
            'siparisler',
            bootstrap_servers=[bootstrap_servers],
            group_id='siparis-isleme-grubu',
            auto_offset_reset='earliest',
            enable_auto_commit=True,
            value_deserializer=lambda x: x.decode('utf-8') if x else None,
            consumer_timeout_ms=1000  # 1 saniye timeout
        )
        
        print("Consumer başlatıldı. Mesajlar bekleniyor...")
        
        for message in consumer:
            if message.value:
                print(f"📦 Sipariş alındı: {message.value} "
                      f"(Partition: {message.partition}, Offset: {message.offset})")
            
    except KeyboardInterrupt:
        print("\n🛑 Consumer durduruldu.")
    except Exception as e:
        print(f"❌ Hata: {e}")
    finally:
        print("Consumer kapatılıyor...")

if __name__ == "__main__":
    main()

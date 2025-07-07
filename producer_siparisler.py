#!/usr/bin/env python3
"""
Siparisler topic'ine mesaj gönderen Producer
Dokümandaki test senaryosuna uygun
"""

from kafka import KafkaProducer
import json
import time
import random
from datetime import datetime

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
    print("Hedef Konu: siparisler")
    print("-" * 50)
    
    try:
        producer = KafkaProducer(
            bootstrap_servers=[bootstrap_servers],
            value_serializer=lambda x: x.encode('utf-8'),
            acks='all',  # Güvenlik için tüm replica'ların onayını bekle
            retries=3
        )
        
        print("Producer başlatıldı. Mesajlar gönderiliyor...")
        
        siparis_id = 1
        
        while True:
            # Rastgele sipariş verisi oluştur
            urunler = ["Laptop", "Telefon", "Tablet", "Kulaklık", "Klavye", "Mouse"]
            urun = random.choice(urunler)
            miktar = random.randint(1, 5)
            fiyat = random.randint(100, 2000)
            
            siparis_data = {
                "siparis_id": siparis_id,
                "urun": urun,
                "miktar": miktar,
                "fiyat": fiyat,
                "tarih": datetime.now().isoformat(),
                "durum": "yeni"
            }
            
            # JSON formatında mesaj gönder
            message = json.dumps(siparis_data, ensure_ascii=False)
            
            future = producer.send('siparisler', value=message)
            result = future.get(timeout=10)  # 10 saniye timeout
            
            print(f"📦 Sipariş #{siparis_id} gönderildi: {urun} x{miktar} = {fiyat}₺ "
                  f"(Partition: {result.partition}, Offset: {result.offset})")
            
            siparis_id += 1
            time.sleep(2)  # 2 saniyede bir mesaj gönder
            
    except KeyboardInterrupt:
        print("\n🛑 Producer durduruldu.")
    except Exception as e:
        print(f"❌ Hata: {e}")
    finally:
        print("Producer kapatılıyor...")
        if 'producer' in locals():
            producer.close()

if __name__ == "__main__":
    main()

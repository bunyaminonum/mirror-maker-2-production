#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DR Consumer - Disaster Recovery Test
Mirror edilen topic'ten mesajları okur
"""

import json
import signal
import sys
from datetime import datetime
from kafka import KafkaConsumer

class DRConsumer:
    def __init__(self):
        # DR Cluster bağlantı bilgileri
        self.bootstrap_servers = 'localhost:9093'  # DR cluster port
        self.topic = 'kaynak.siparisler'  # Mirror edilen topic
        self.consumer_group = 'siparis-dr-grubu'  # DR consumer group
        
        self.consumer = None
        self.running = True
        
        # Graceful shutdown için signal handler
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def signal_handler(self, signum, frame):
        """Signal handler for graceful shutdown"""
        print(f"\n🔴 Signal {signum} alındı. Consumer kapatılıyor...")
        self.running = False
    
    def create_consumer(self):
        """Kafka consumer oluştur"""
        try:
            self.consumer = KafkaConsumer(
                self.topic,
                bootstrap_servers=self.bootstrap_servers,
                group_id=self.consumer_group,
                auto_offset_reset='earliest',  # En baştan oku
                enable_auto_commit=True,
                auto_commit_interval_ms=1000,
                value_deserializer=lambda v: json.loads(v.decode('utf-8')) if v else None,
                consumer_timeout_ms=10000  # 10 saniye timeout
            )
            return True
        except Exception as e:
            print(f"❌ Consumer oluşturulamadı: {e}")
            return False
    
    def start_consuming(self):
        """Mesaj tüketmeye başla"""
        print("🔄 DR CLUSTER TEST")
        print("=" * 50)
        print(f"🎯 DR Cluster: localhost:9093")
        print(f"📂 Mirror Topic: {self.topic}")
        print(f"👥 Consumer Group: {self.consumer_group}")
        print("=" * 50)
        
        if not self.create_consumer():
            return
        
        print("🚀 DR Consumer başlatıldı. Mirror edilen mesajlar okunuyor...")
        print("💡 CTRL+C ile durdurun")
        print("-" * 50)
        
        message_count = 0
        
        try:
            for message in self.consumer:
                if not self.running:
                    break
                
                message_count += 1
                
                # Mesaj bilgilerini göster
                siparis = message.value
                partition = message.partition
                offset = message.offset
                timestamp = datetime.fromtimestamp(message.timestamp / 1000).strftime('%Y-%m-%d %H:%M:%S')
                
                print(f"📦 DR Mesaj #{message_count}: Sipariş #{siparis['siparis_id']} - "
                      f"{siparis['urun']} x{siparis['miktar']} = {siparis['fiyat']}₺ "
                      f"(P:{partition}, O:{offset}, T:{timestamp})")
                
                # Her 10 mesajda bir özet
                if message_count % 10 == 0:
                    print(f"📊 Toplam {message_count} DR mesaj işlendi...")
                    
        except Exception as e:
            print(f"❌ Consumer hatası: {e}")
        finally:
            if self.consumer:
                print("\n🔄 DR Consumer kapatılıyor...")
                self.consumer.close()
                print(f"✅ Toplam {message_count} DR mesaj işlendi.")

def main():
    """Ana fonksiyon"""
    dr_consumer = DRConsumer()
    dr_consumer.start_consuming()

if __name__ == "__main__":
    main()

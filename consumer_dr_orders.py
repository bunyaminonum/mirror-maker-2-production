#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DR Consumer - Disaster Recovery Test
Reads messages from mirrored topic
"""

import json
import signal
import sys
from datetime import datetime
from kafka import KafkaConsumer

class DRConsumer:
    def __init__(self):
        # DR Cluster connection info
        self.bootstrap_servers = 'localhost:9093'  # DR cluster port
        self.topic = 'source.orders'  # Mirrored topic
        self.consumer_group = 'order-dr-group'  # DR consumer group
        
        self.consumer = None
        self.running = True
        
        # Signal handler for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def signal_handler(self, signum, frame):
        """Signal handler for graceful shutdown"""
        print(f"\n🔴 Signal {signum} received. Closing consumer...")
        self.running = False
    
    def create_consumer(self):
        """Create Kafka consumer"""
        try:
            self.consumer = KafkaConsumer(
                self.topic,
                bootstrap_servers=self.bootstrap_servers,
                group_id=self.consumer_group,
                auto_offset_reset='earliest',  # Read from beginning
                enable_auto_commit=True,
                auto_commit_interval_ms=1000,
                value_deserializer=lambda v: json.loads(v.decode('utf-8')) if v else None,
                consumer_timeout_ms=10000  # 10 second timeout
            )
            return True
        except Exception as e:
            print(f"❌ Consumer could not be created: {e}")
            return False
    
    def start_consuming(self):
        """Start consuming messages"""
        print("🔄 DR CLUSTER TEST")
        print("=" * 50)
        print(f"🎯 DR Cluster: localhost:9093")
        print(f"📂 Mirror Topic: {self.topic}")
        print(f"👥 Consumer Group: {self.consumer_group}")
        print("=" * 50)
        
        if not self.create_consumer():
            return
        
        print("🚀 DR Consumer started. Reading mirrored messages...")
        print("💡 Stop with CTRL+C")
        print("-" * 50)
        
        message_count = 0
        
        try:
            for message in self.consumer:
                if not self.running:
                    break
                
                message_count += 1
                
                # Show message info
                order = message.value
                partition = message.partition
                offset = message.offset
                timestamp = datetime.fromtimestamp(message.timestamp / 1000).strftime('%Y-%m-%d %H:%M:%S')
                
                print(f"📦 DR Message #{message_count}: Order #{order['order_id']} - "
                      f"{order['product']} x{order['quantity']} = ${order['price']} "
                      f"(P:{partition}, O:{offset}, T:{timestamp})")
                
                # Summary every 10 messages
                if message_count % 10 == 0:
                    print(f"📊 Total {message_count} DR messages processed...")
                    
        except Exception as e:
            print(f"❌ Consumer error: {e}")
        finally:
            if self.consumer:
                print("\n🔄 Closing DR Consumer...")
                self.consumer.close()
                print(f"✅ Total {message_count} DR messages processed.")

def main():
    """Main function"""
    dr_consumer = DRConsumer()
    dr_consumer.start_consuming()

if __name__ == "__main__":
    main()

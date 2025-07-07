#!/usr/bin/env python3
"""
Orders topic consumer
Suitable for test scenarios in documentation
"""

from kafka import KafkaConsumer
import json
import time
import sys

def main():
    # Active cluster information is manually specified (for simple test)
    # In real application this would be read from Consul
    
    CLUSTER_CONFIG = {
        'source': 'localhost:9092',
        'target': 'localhost:9093'
    }
    
    # Currently using source cluster
    active_cluster = 'source'
    bootstrap_servers = CLUSTER_CONFIG[active_cluster]
    
    print(f"Active cluster: {active_cluster}")
    print(f"Bootstrap servers: {bootstrap_servers}")
    print("Listening topic: orders")
    print("Consumer Group: order-processing-group")
    print("-" * 50)
    
    try:
        consumer = KafkaConsumer(
            'orders',
            bootstrap_servers=[bootstrap_servers],
            group_id='order-processing-group',
            auto_offset_reset='earliest',
            enable_auto_commit=True,
            value_deserializer=lambda x: x.decode('utf-8') if x else None,
            consumer_timeout_ms=1000  # 1 second timeout
        )
        
        print("Consumer started. Waiting for messages...")
        
        for message in consumer:
            if message.value:
                print(f"📦 Order received: {message.value} "
                      f"(Partition: {message.partition}, Offset: {message.offset})")
            
    except KeyboardInterrupt:
        print("\n🛑 Consumer stopped.")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        print("Closing consumer...")

if __name__ == "__main__":
    main()

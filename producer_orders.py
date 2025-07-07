#!/usr/bin/env python3
"""
Orders topic message producer
Suitable for test scenarios in documentation
"""

from kafka import KafkaProducer
import json
import time
import random
from datetime import datetime

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
    print("Target topic: orders")
    print("-" * 50)
    
    try:
        producer = KafkaProducer(
            bootstrap_servers=[bootstrap_servers],
            value_serializer=lambda x: x.encode('utf-8'),
            acks='all',  # Güvenlik için tüm replica'ların onayını bekle
            retries=3
        )
        
        print("Producer başlatıldı. Mesajlar gönderiliyor...")
        
        order_id = 1
        
        while True:
            # Generate random order data
            products = ["Laptop", "Phone", "Tablet", "Headphone", "Keyboard", "Mouse"]
            product = random.choice(products)
            quantity = random.randint(1, 5)
            price = random.randint(100, 2000)
            
            order_data = {
                "order_id": order_id,
                "product": product,
                "quantity": quantity,
                "price": price,
                "timestamp": datetime.now().isoformat(),
                "status": "new"
            }
            
            # Send message in JSON format
            message = json.dumps(order_data, ensure_ascii=False)
            
            future = producer.send('orders', value=message)
            result = future.get(timeout=10)  # 10 second timeout
            
            print(f"📦 Order #{order_id} sent: {product} x{quantity} = ${price} "
                  f"(Partition: {result.partition}, Offset: {result.offset})")
            
            order_id += 1
            time.sleep(2)  # Send a message every 2 seconds
            
    except KeyboardInterrupt:
        print("\n🛑 Producer stopped.")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        print("Closing producer...")
        if 'producer' in locals():
            producer.close()

if __name__ == "__main__":
    main()

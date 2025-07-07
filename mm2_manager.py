#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MM2 Connector Management Script
Production-Ready Mirror Maker 2 Cluster Management
"""

import json
import requests
import time
import sys
from pathlib import Path

class MM2ConnectorManager:
    def __init__(self, connect_url="http://localhost:8083"):
        self.connect_url = connect_url
        self.connector_configs_dir = Path("connect")
        
    def wait_for_connect(self, max_retries=30):
        """Connect cluster'ın hazır olmasını bekle"""
        print("🔄 Kafka Connect cluster'ın hazır olması bekleniyor...")
        
        for i in range(max_retries):
            try:
                response = requests.get(f"{self.connect_url}/")
                if response.status_code == 200:
                    print("✅ Kafka Connect cluster hazır!")
                    return True
            except requests.exceptions.ConnectionError:
                pass
            
            print(f"⏳ Bekleniyor... ({i+1}/{max_retries})")
            time.sleep(5)
        
        print("❌ Kafka Connect cluster'a bağlanılamadı!")
        return False
    
    def get_connectors(self):
        """Mevcut connector'ları listele"""
        try:
            response = requests.get(f"{self.connect_url}/connectors")
            if response.status_code == 200:
                return response.json()
            return []
        except Exception as e:
            print(f"❌ Connector listesi alınamadı: {e}")
            return []
    
    def get_connector_status(self, connector_name):
        """Connector durumunu kontrol et"""
        try:
            response = requests.get(f"{self.connect_url}/connectors/{connector_name}/status")
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            print(f"❌ {connector_name} durumu alınamadı: {e}")
            return None
    
    def create_connector(self, config_file):
        """Connector oluştur"""
        config_path = self.connector_configs_dir / config_file
        
        if not config_path.exists():
            print(f"❌ Konfigürasyon dosyası bulunamadı: {config_path}")
            return False
        
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            connector_name = config["name"]
            
            # Mevcut connector'ı sil
            self.delete_connector(connector_name)
            time.sleep(2)
            
            # Yeni connector oluştur
            response = requests.post(
                f"{self.connect_url}/connectors",
                headers={"Content-Type": "application/json"},
                json=config
            )
            
            if response.status_code in [200, 201]:
                print(f"✅ {connector_name} başarıyla oluşturuldu")
                return True
            else:
                print(f"❌ {connector_name} oluşturulamadı: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ {config_file} oluşturulamadı: {e}")
            return False
    
    def delete_connector(self, connector_name):
        """Connector'ı sil"""
        try:
            response = requests.delete(f"{self.connect_url}/connectors/{connector_name}")
            if response.status_code in [200, 204, 404]:
                if response.status_code != 404:
                    print(f"🗑️ {connector_name} silindi")
                return True
            else:
                print(f"❌ {connector_name} silinemedi: {response.text}")
                return False
        except Exception as e:
            print(f"❌ {connector_name} silinemedi: {e}")
            return False
    
    def deploy_all_connectors(self):
        """Tüm MM2 connector'larını deploy et"""
        print("🚀 MM2 Connector'lar deploy ediliyor...")
        
        connectors = [
            "mm2-source-connector.json",
            "mm2-heartbeat-connector.json", 
            "mm2-checkpoint-connector.json"
        ]
        
        success_count = 0
        for connector_file in connectors:
            if self.create_connector(connector_file):
                success_count += 1
                time.sleep(3)  # Connector'lar arası bekleme
        
        print(f"\n📊 Deployment Sonucu: {success_count}/{len(connectors)} connector başarılı")
        return success_count == len(connectors)
    
    def show_cluster_status(self):
        """Cluster durumunu göster"""
        print("\n📊 MM2 CLUSTER DURUMU")
        print("=" * 50)
        
        # Connect cluster durumu
        try:
            response = requests.get(f"{self.connect_url}/")
            if response.status_code == 200:
                print("✅ Kafka Connect Cluster: RUNNING")
            else:
                print("❌ Kafka Connect Cluster: ERROR")
        except:
            print("❌ Kafka Connect Cluster: UNREACHABLE")
        
        # Connector durumları
        connectors = self.get_connectors()
        print(f"\n🔗 Active Connectors: {len(connectors)}")
        
        for connector_name in connectors:
            status = self.get_connector_status(connector_name)
            if status:
                state = status.get("connector", {}).get("state", "UNKNOWN")
                tasks = status.get("tasks", [])
                task_states = [task.get("state", "UNKNOWN") for task in tasks]
                
                print(f"  📌 {connector_name}: {state}")
                for i, task_state in enumerate(task_states):
                    print(f"    └─ Task {i}: {task_state}")
        
        print("=" * 50)

def main():
    if len(sys.argv) < 2:
        print("Kullanım:")
        print("  python mm2_manager.py deploy    - Tüm connector'ları deploy et")
        print("  python mm2_manager.py status    - Cluster durumunu göster")
        print("  python mm2_manager.py delete    - Tüm connector'ları sil")
        return
    
    manager = MM2ConnectorManager()
    command = sys.argv[1].lower()
    
    if command == "deploy":
        if not manager.wait_for_connect():
            sys.exit(1)
        manager.deploy_all_connectors()
        time.sleep(5)
        manager.show_cluster_status()
        
    elif command == "status":
        manager.show_cluster_status()
        
    elif command == "delete":
        connectors = ["MirrorSourceConnector", "MirrorHeartbeatConnector", "MirrorCheckpointConnector"]
        for connector in connectors:
            manager.delete_connector(connector)
        print("🗑️ Tüm connector'lar silindi")
        
    else:
        print(f"❌ Bilinmeyen komut: {command}")

if __name__ == "__main__":
    main()

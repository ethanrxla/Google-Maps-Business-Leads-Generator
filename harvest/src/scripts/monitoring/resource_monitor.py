#!/usr/bin/env python3
"""
Resource monitoring for WSL environment
"""

import psutil
import time
import threading
from datetime import datetime

class ResourceMonitor:
    def __init__(self, interval=5):
        self.interval = interval
        self.monitoring = False
        self.data = []
    
    def start(self):
        """Start resource monitoring"""
        self.monitoring = True
        print("[*] Starting resource monitor...")
        
        try:
            while self.monitoring:
                snapshot = self.take_snapshot()
                self.data.append(snapshot)
                self.display_status(snapshot)
                time.sleep(self.interval)
        except KeyboardInterrupt:
            self.stop()
    
    def take_snapshot(self) -> dict:
        """Take resource usage snapshot"""
        return {
            'timestamp': datetime.now(),
            'cpu_percent': psutil.cpu_percent(),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_usage': psutil.disk_usage('/').percent,
            'network_io': psutil.net_io_counters()
        }
    
    def display_status(self, snapshot):
        """Display current resource status"""
        print(f"\r[*] CPU: {snapshot['cpu_percent']:.1f}% | "
              f"Memory: {snapshot['memory_percent']:.1f}% | "
              f"Disk: {snapshot['disk_usage']:.1f}%", end="")
    
    def stop(self):
        """Stop monitoring and generate report"""
        self.monitoring = False
        print("\n[*] Resource monitoring stopped")
        self.generate_report()
    
    def generate_report(self):
        """Generate monitoring report"""
        if not self.data:
            return
        
        print("\n" + "="*50)
        print("RESOURCE MONITORING REPORT")
        print("="*50)
        
        # Calculate averages
        avg_cpu = sum(s['cpu_percent'] for s in self.data) / len(self.data)
        avg_memory = sum(s['memory_percent'] for s in self.data) / len(self.data)
        
        print(f"Monitoring Duration: {len(self.data) * self.interval} seconds")
        print(f"Average CPU Usage: {avg_cpu:.1f}%")
        print(f"Average Memory Usage: {avg_memory:.1f}%")
        print(f"Data Points Collected: {len(self.data)}")
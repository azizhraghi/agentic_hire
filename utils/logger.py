import logging
from datetime import datetime

class HackathonLogger:
    """Logger simple pour le hackathon"""
    
    def __init__(self, name: str):
        self.name = name
        
    def info(self, message: str):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] [ℹ️] [{self.name}] {message}")
    
    def success(self, message: str):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] [✅] [{self.name}] {message}")
    
    def warning(self, message: str):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] [⚠️] [{self.name}] {message}")
    
    def error(self, message: str):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] [❌] [{self.name}] {message}")
    
    def data(self, data: dict):
        print(f"[📊] Données extraites:")
        import json
        print(json.dumps(data, indent=2, ensure_ascii=False))
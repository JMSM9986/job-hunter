import json
from pathlib import Path
from typing import Dict, Any, Optional

class JobCache:
    """Cache persistente local para evitar reavaliação de vagas já analisadas nas últimas 24 horas."""
    
    def __init__(self, cache_file: str = ".job_cache.json"):
        self.cache_file = Path(cache_file)
        self.data: Dict[str, Any] = {}
        self._load()

    def _load(self):
        if self.cache_file.exists():
            try:
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    self.data = json.load(f)
            except Exception:
                self.data = {}

    def save(self):
        try:
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def get(self, url: str) -> Optional[Dict[str, Any]]:
        return self.data.get(url)

    def set(self, url: str, info: Dict[str, Any]):
        self.data[url] = info

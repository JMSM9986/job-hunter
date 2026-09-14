from abc import ABC, abstractmethod
from typing import List, Optional
import httpx
from ..models import JobOffer

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "pt-PT,pt;q=0.9,en-US;q=0.8,en;q=0.7",
    "Cache-Control": "no-cache",
}

class BaseScraper(ABC):
    """Classe base abstrata para todos os scrapers de portais de emprego."""
    
    def __init__(self, name: str, base_url: str):
        self.name = name
        self.base_url = base_url
        self.client = httpx.Client(
            headers=DEFAULT_HEADERS,
            timeout=5.0,
            limits=httpx.Limits(max_keepalive_connections=20, max_connections=40),
            follow_redirects=True,
            verify=True
        )

    @abstractmethod
    def search(self, keywords: List[str], max_days: int = 15, location: str = "Lisboa") -> List[JobOffer]:
        """Executa a pesquisa no portal e devolve uma lista de JobOffer."""
        pass

    def close(self):
        self.client.close()

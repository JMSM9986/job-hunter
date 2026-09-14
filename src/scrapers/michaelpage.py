import re
import urllib.parse
from datetime import datetime, timedelta
from typing import List
from bs4 import BeautifulSoup
from .base import BaseScraper
from ..models import JobOffer

class MichaelPageScraper(BaseScraper):
    """Scraper para o portal Michael Page Portugal (Recrutamento Especializado de Gestão e Finanças)."""
    
    def __init__(self):
        super().__init__(name="Michael Page", base_url="https://www.michaelpage.pt")

    def search(self, keywords: List[str], max_days: int = 15, location: str = "Lisboa") -> List[JobOffer]:
        offers: List[JobOffer] = []
        now = datetime.now()
        seen_urls = set()

        categories = [
            "/jobs/consultoria-gest%C3%A3o/lisboa",
            "/jobs/banca-servi%C3%A7os-financeiros/lisboa"
        ]

        for cat in categories:
            url = f"{self.base_url}{cat}"
            try:
                resp = self.client.get(url, timeout=7.0)
                if resp.status_code != 200:
                    continue

                soup = BeautifulSoup(resp.text, "html.parser")
                links = soup.select('a[href*="/job-detail/"]')

                for a in links:
                    href = a.get("href")
                    if not href:
                        continue
                    full_url = urllib.parse.urljoin(self.base_url, href)
                    if full_url in seen_urls:
                        continue

                    title = a.get_text(strip=True)
                    if not title or title.lower() in ["detalhes da oferta", "ver oferta", "candidatar"]:
                        continue

                    seen_urls.add(full_url)
                    
                    # Assume publicado recente (listagem ativa Michael Page)
                    pub_date = now - timedelta(days=2)
                    days_ago = 2

                    title_lower = title.lower()
                    is_part_time = "part-time" in title_lower or "part time" in title_lower
                    is_remote = "remoto" in title_lower or "remote" in title_lower or "híbrido" in title_lower

                    offer_id = f"mp_{re.sub(r'[^a-zA-Z0-9]', '', full_url)[-20:]}"
                    offers.append(JobOffer(
                        id=offer_id,
                        title=title,
                        company="Michael Page (Cliente Confidencial)",
                        location=location if not is_remote else f"{location} / Remoto",
                        is_remote=is_remote,
                        is_part_time=is_part_time,
                        publication_date=pub_date,
                        published_days_ago=days_ago,
                        url=full_url,
                        source_portal=self.name,
                        description=f"Oportunidade de gestão executiva Michael Page: {title} em Lisboa"
                    ))
            except Exception:
                continue

        return offers

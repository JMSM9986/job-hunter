import re
import urllib.parse
from datetime import datetime, timedelta
from typing import List
from bs4 import BeautifulSoup
from .base import BaseScraper
from ..models import JobOffer

class HaysScraper(BaseScraper):
    """Scraper para o portal Hays Portugal (Média e Alta Direção)."""
    
    def __init__(self):
        super().__init__(name="Hays Portugal", base_url="https://www.hays.pt")

    def search(self, keywords: List[str], max_days: int = 15, location: str = "Lisboa") -> List[JobOffer]:
        offers: List[JobOffer] = []
        now = datetime.now()
        seen_urls = set()

        categories = [
            "/emprego/banca",
            "/emprego/consultoria",
            "/emprego/contabilidade-financas",
            "/emprego/auditoria"
        ]

        for cat in categories:
            url = f"{self.base_url}{cat}"
            try:
                resp = self.client.get(url, timeout=7.0)
                if resp.status_code != 200:
                    continue

                soup = BeautifulSoup(resp.text, "html.parser")
                job_links = soup.select('a[href*="/detalhes-oferta/"]')

                for a in job_links:
                    href = a.get("href")
                    if not href:
                        continue
                    full_url = urllib.parse.urljoin(self.base_url, href)
                    if full_url in seen_urls:
                        continue

                    title_text = a.get_text(strip=True)
                    if not title_text:
                        continue

                    seen_urls.add(full_url)

                    # Tenta separar título e localização se vierem colados (ex: "Diretor Financeiro (m/f)Lisboa")
                    loc_match = re.search(r'(Lisboa|Porto|Remoto|Portugal)$', title_text, re.IGNORECASE)
                    job_loc = loc_match.group(1) if loc_match else location
                    clean_title = title_text[:loc_match.start()].strip() if loc_match else title_text

                    # Se a localização for fora de Lisboa e não for remoto, descarta
                    if "porto" in job_loc.lower():
                        continue

                    pub_date = now - timedelta(days=2)
                    days_ago = 2

                    title_lower = clean_title.lower()
                    is_part_time = "part-time" in title_lower or "part time" in title_lower
                    is_remote = "remoto" in title_lower or "remote" in title_lower or "híbrido" in title_lower

                    offer_id = f"hays_{re.sub(r'[^a-zA-Z0-9]', '', full_url)[-20:]}"
                    offers.append(JobOffer(
                        id=offer_id,
                        title=clean_title,
                        company="Hays Executive Search",
                        location=job_loc,
                        is_remote=is_remote,
                        is_part_time=is_part_time,
                        publication_date=pub_date,
                        published_days_ago=days_ago,
                        url=full_url,
                        source_portal=self.name,
                        description=f"Oportunidade executiva Hays Portugal: {clean_title} ({job_loc})"
                    ))
            except Exception:
                continue

        return offers

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
            "/jobs/banking-financial-services/grande-lisboa",
            "/jobs/consultancy-strategy-change/grande-lisboa",
            "/jobs/accounting/grande-lisboa"
        ]

        for cat in categories:
            url = f"{self.base_url}{cat}"
            try:
                resp = self.client.get(url, timeout=8.0)
                if resp.status_code != 200:
                    continue

                soup = BeautifulSoup(resp.text, "html.parser")
                tiles = soup.select(".job-tile")

                for t in tiles:
                    title_a = t.select_one(".job-title a, a[href*='/job-detail/']")
                    if not title_a or not title_a.get("href"):
                        continue

                    href = title_a["href"]
                    full_url = urllib.parse.urljoin(self.base_url, href)
                    if full_url in seen_urls:
                        continue
                    seen_urls.add(full_url)

                    title = title_a.get_text(strip=True)
                    if not title or title.lower() in ["detalhes da oferta", "ver oferta", "candidatar"]:
                        continue

                    # Extrair resumo do anúncio
                    sum_el = t.select_one(".job-summary p, .job_advert__job-summary-text p")
                    summary_text = sum_el.get_text(" ", strip=True) if sum_el else ""

                    # Extrair localização
                    loc_el = t.select_one(".job-location")
                    job_loc = loc_el.get_text(strip=True) if loc_el else location

                    # Assume publicado recente (listagem ativa Michael Page)
                    pub_date = now - timedelta(days=2)
                    days_ago = 2

                    card_text = f"{title} {summary_text}".lower()
                    is_part_time = "part-time" in card_text or "part time" in card_text or "parcial" in card_text
                    is_remote = "remoto" in card_text or "remote" in card_text or "híbrido" in card_text or "hybrid" in card_text

                    offer_id = f"mp_{re.sub(r'[^a-zA-Z0-9]', '', full_url)[-20:]}"
                    offers.append(JobOffer(
                        id=offer_id,
                        title=title,
                        company="Michael Page (Mandato Executivo)",
                        location=job_loc,
                        is_remote=is_remote,
                        is_part_time=is_part_time,
                        publication_date=pub_date,
                        published_days_ago=days_ago,
                        url=full_url,
                        source_portal=self.name,
                        description=summary_text or f"Oportunidade de gestão executiva Michael Page: {title} em Lisboa"
                    ))
            except Exception:
                continue

        return offers

import re
import urllib.parse
from datetime import datetime, timedelta
from typing import List, Optional
from bs4 import BeautifulSoup
from .base import BaseScraper
from ..models import JobOffer

class SapoEmpregoScraper(BaseScraper):
    """Scraper para o portal Sapo Emprego (Generalista, Gestão, Finanças e Assessoria)."""
    
    def __init__(self):
        super().__init__(name="Sapo Emprego", base_url="https://emprego.sapo.pt")

    def _parse_days(self, text: str) -> int:
        match = re.search(r'(\d+)\s*dias?', text, re.IGNORECASE)
        if match:
            return int(match.group(1))
        if "ontem" in text.lower():
            return 1
        if "hoje" in text.lower() or "hora" in text.lower() or "minuto" in text.lower():
            return 0
        return 0

    def search(self, keywords: List[str], max_days: int = 15, location: str = "Lisboa") -> List[JobOffer]:
        offers: List[JobOffer] = []
        now = datetime.now()
        seen_urls = set()

        for kw in keywords:
            encoded_kw = urllib.parse.quote_plus(kw)
            search_url = f"{self.base_url}/ofertas/pesquisa?q={encoded_kw}&localidade={location}"
            
            try:
                resp = self.client.get(search_url)
                if resp.status_code != 200:
                    continue
                    
                soup = BeautifulSoup(resp.text, "html.parser")
                items = soup.select(".offer-item, .card-job, article")

                for item in items:
                    title_el = item.select_one(".offer-title a, h2 a, h3 a, a.job-title")
                    if not title_el or not title_el.get("href"):
                        continue
                        
                    full_url = urllib.parse.urljoin(self.base_url, title_el["href"])
                    if full_url in seen_urls:
                        continue
                    seen_urls.add(full_url)
                    
                    title = title_el.get_text(strip=True)
                    
                    # Empresa
                    comp_el = item.select_one(".offer-company, .company, span.empresa")
                    company = comp_el.get_text(strip=True) if comp_el else "Confidencial"
                    
                    # Data
                    date_el = item.select_one(".offer-date, .date, time")
                    date_str = date_el.get_text(strip=True) if date_el else ""
                    days_ago = self._parse_days(date_str)
                    
                    if days_ago > max_days:
                        continue
                        
                    pub_date = now - timedelta(days=days_ago)
                    
                    raw_text = item.get_text(" ", strip=True).lower()
                    is_part_time = "part-time" in raw_text or "part time" in raw_text
                    is_remote = "remoto" in raw_text or "teletrabalho" in raw_text or "híbrido" in raw_text
                    
                    desc_el = item.select_one(".offer-description, .description, p")
                    desc = desc_el.get_text(" ", strip=True) if desc_el else ""
                    
                    offer_id = f"sapo_{re.sub(r'[^a-zA-Z0-9]', '', full_url)[-20:]}"
                    offers.append(JobOffer(
                        id=offer_id,
                        title=title,
                        company=company,
                        location=location if not is_remote else f"{location} / Remoto",
                        is_remote=is_remote,
                        is_part_time=is_part_time,
                        publication_date=pub_date,
                        published_days_ago=days_ago,
                        url=full_url,
                        source_portal=self.name,
                        description=desc
                    ))
            except Exception:
                continue

        return offers

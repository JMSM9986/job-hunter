import re
import urllib.parse
from datetime import datetime, timedelta
from typing import List, Optional
from bs4 import BeautifulSoup
from .base import BaseScraper
from ..models import JobOffer

class AlertaEmpregoScraper(BaseScraper):
    """Scraper para o portal Alerta Emprego (Ofertas de Gestão, Finanças, Lisboa)."""
    
    def __init__(self):
        super().__init__(name="Alerta Emprego", base_url="https://www.alertaemprego.pt")

    def search(self, keywords: List[str], max_days: int = 15, location: str = "Lisboa") -> List[JobOffer]:
        offers: List[JobOffer] = []
        now = datetime.now()
        seen_urls = set()

        for kw in keywords:
            encoded_kw = urllib.parse.quote_plus(kw)
            search_url = f"{self.base_url}/emprego?q={encoded_kw}&distrito=11" # 11 = Lisboa
            
            try:
                resp = self.client.get(search_url)
                if resp.status_code != 200:
                    continue
                    
                soup = BeautifulSoup(resp.text, "html.parser")
                job_elements = soup.select(".job-offer, .job-item, article.job")

                for el in job_elements:
                    title_a = el.select_one("h2 a, h3 a, a.job-title, a.title")
                    if not title_a or not title_a.get("href"):
                        continue
                        
                    full_url = urllib.parse.urljoin(self.base_url, title_a["href"])
                    if full_url in seen_urls:
                        continue
                    seen_urls.add(full_url)
                    
                    title = title_a.get_text(strip=True)
                    
                    company_el = el.select_one(".company, .employer, span.empresa")
                    company = company_el.get_text(strip=True) if company_el else "Confidencial"
                    
                    text_content = el.get_text(" ", strip=True).lower()
                    is_part_time = "part-time" in text_content or "part time" in text_content
                    is_remote = "remoto" in text_content or "teletrabalho" in text_content or "híbrido" in text_content
                    
                    # Assume publicado recente na listagem atual
                    pub_date = now - timedelta(days=2)
                    days_ago = 2
                    
                    desc_el = el.select_one(".description, p")
                    desc = desc_el.get_text(" ", strip=True) if desc_el else ""
                    
                    offer_id = f"alerta_{re.sub(r'[^a-zA-Z0-9]', '', full_url)[-20:]}"
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

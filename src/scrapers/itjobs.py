import re
import urllib.parse
from datetime import datetime, timedelta
from typing import List, Optional
import feedparser
from bs4 import BeautifulSoup
from .base import BaseScraper
from ..models import JobOffer

class ITJobsScraper(BaseScraper):
    """Scraper para o portal ITJobs.pt (Tecnologia, Fintech, Gestão e Consultoria)."""
    
    def __init__(self):
        super().__init__(name="ITJobs.pt", base_url="https://www.itjobs.pt")

    def _parse_date(self, date_str: str) -> Optional[datetime]:
        match = re.search(r'(\d{1,2})[-/](\d{1,2})[-/](\d{4})', date_str)
        if match:
            day, month, year = map(int, match.groups())
            try:
                return datetime(year, month, day)
            except ValueError:
                return None
        return None

    def search(self, keywords: List[str], max_days: int = 15, location: str = "Lisboa") -> List[JobOffer]:
        offers: List[JobOffer] = []
        now = datetime.now()
        cutoff_date = now - timedelta(days=max_days)
        seen_urls = set()

        for kw in keywords:
            encoded_kw = urllib.parse.quote_plus(kw)
            search_url = f"{self.base_url}/emprego?q={encoded_kw}&location=14" # 14 = Lisboa
            
            try:
                resp = self.client.get(search_url)
                if resp.status_code != 200:
                    continue
                    
                soup = BeautifulSoup(resp.text, "html.parser")
                job_blocks = soup.select(".list .item, .job-item, article.job")

                for block in job_blocks:
                    title_tag = block.select_one(".title a, h2 a, h3 a")
                    if not title_tag or not title_tag.get("href"):
                        continue
                        
                    full_url = urllib.parse.urljoin(self.base_url, title_tag["href"])
                    if full_url in seen_urls:
                        continue
                    seen_urls.add(full_url)
                    
                    title = title_tag.get_text(strip=True)
                    
                    # Empresa
                    comp_tag = block.select_one(".company a, .company, .employer")
                    company = comp_tag.get_text(strip=True) if comp_tag else "Confidencial"
                    
                    # Data
                    date_tag = block.select_one(".date, time, .time")
                    date_text = date_tag.get_text(strip=True) if date_tag else ""
                    pub_date = self._parse_date(date_text) or now
                    
                    days_ago = (now - pub_date).days
                    if days_ago > max_days or days_ago < 0:
                        continue
                        
                    # Detalhes de texto
                    text_content = block.get_text(" ", strip=True).lower()
                    is_part_time = "part-time" in text_content or "part time" in text_content or "parcial" in text_content
                    is_remote = "remoto" in text_content or "remote" in text_content or "teletrabalho" in text_content or "híbrido" in text_content
                    
                    desc_tag = block.select_one(".body, .description, p")
                    desc = desc_tag.get_text(" ", strip=True) if desc_tag else ""
                    
                    offer_id = f"itj_{re.sub(r'[^a-zA-Z0-9]', '', full_url)[-20:]}"
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

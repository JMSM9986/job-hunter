import re
import urllib.parse
from datetime import datetime
from typing import List, Optional
import concurrent.futures
from bs4 import BeautifulSoup
from .base import BaseScraper
from ..models import JobOffer

class ExpressoEmpregoScraper(BaseScraper):
    """Scraper para o portal Expresso Emprego (Grupo Impresa / Jornal Expresso)."""
    
    def __init__(self):
        super().__init__(name="Expresso Emprego", base_url="https://expressoemprego.pt")

    def search(self, keywords: List[str], max_days: int = 15, location: str = "Lisboa") -> List[JobOffer]:
        offers: List[JobOffer] = []
        now = datetime.now()
        seen_urls = set()

        # Consultas direcionadas no Expresso Emprego
        target_queries = [
            "diretor-financeiro",
            "cfo",
            "controller",
            "corporate-finance",
            "economia",
            "consultor"
        ]

        urls_to_fetch = [f"{self.base_url}/emprego/pesquisa/{q}/lisboa?order=data" for q in target_queries]

        def _fetch(url):
            try:
                resp = self.client.get(url, timeout=5.0)
                if resp.status_code == 200:
                    return resp.text
            except Exception:
                return None
            return None

        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
            html_results = executor.map(_fetch, urls_to_fetch)

        for html_content in html_results:
            if not html_content:
                continue

            try:
                soup = BeautifulSoup(html_content, "html.parser")
                boxes = soup.select(".resultadosBox")

                for b in boxes:
                    title_tag = b.select_one("h3 a")
                    if not title_tag or not title_tag.get("href"):
                        continue

                    href = title_tag["href"]
                    full_url = f"{self.base_url}{href}" if href.startswith("/") else href
                    if full_url in seen_urls:
                        continue
                    seen_urls.add(full_url)

                    title = title_tag.get_text(strip=True)
                    comp_tag = b.select_one("h4")
                    company = comp_tag.get_text(strip=True) if comp_tag else "Confidencial"

                    box_text = b.get_text(" | ", strip=True)
                    date_match = re.search(r"(\d{2})\.(\d{2})\.(\d{4})", box_text)
                    pub_date = now
                    days_ago = 1
                    if date_match:
                        try:
                            d, m, y = map(int, date_match.groups())
                            pub_date = datetime(y, m, d)
                            days_ago = max(0, (now - pub_date).days)
                        except Exception:
                            pass

                    # Localização
                    loc_str = "Lisboa"
                    if "lisboa" in box_text.lower():
                        loc_str = "Lisboa"

                    is_part_time = "part-time" in box_text.lower() or "parcial" in box_text.lower()
                    is_remote = "remoto" in box_text.lower() or "teletrabalho" in box_text.lower() or "híbrido" in box_text.lower() or "hybrid" in box_text.lower()

                    offer_id = f"exp_{re.sub(r'[^a-zA-Z0-9]', '', full_url)[-20:]}"
                    offers.append(JobOffer(
                        id=offer_id,
                        title=title,
                        company=company,
                        location=loc_str,
                        is_remote=is_remote,
                        is_part_time=is_part_time,
                        publication_date=pub_date,
                        published_days_ago=days_ago,
                        url=full_url,
                        source_portal=self.name,
                        description=f"Vaga no Expresso Emprego: {title} na {company} ({loc_str}). {box_text[:200]}"
                    ))

            except Exception:
                continue

        return offers

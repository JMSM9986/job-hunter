import re
import urllib.parse
from datetime import datetime, timedelta
from typing import List, Optional
from bs4 import BeautifulSoup
from .base import BaseScraper
from ..models import JobOffer

class LinkedInPublicScraper(BaseScraper):
    """Scraper para ofertas públicas de emprego no LinkedIn Portugal (sem necessidade de login)."""
    
    def __init__(self):
        super().__init__(name="LinkedIn Jobs", base_url="https://www.linkedin.com")

    def search(self, keywords: List[str], max_days: int = 15, location: str = "Lisbon, Portugal") -> List[JobOffer]:
        offers: List[JobOffer] = []
        now = datetime.now()
        seen_urls = set()
        
        import concurrent.futures
        tpr_seconds = max_days * 86400

        # Localização ótima para API do LinkedIn Portugal
        target_loc = "Lisbon, Portugal" if "lisbo" in location.lower() or location.lower() == "portugal" else location

        # Termos específicos focados nos 5 perfis pretendidos + ofertas de Bancos
        core_linkedin_queries = [
            # 1. Direção Financeira & CFO
            "diretor financeiro",
            "cfo",
            "head of finance",
            "financial controller",
            "finance director",
            # 2. Consultoria & Assessoria
            "consultor economico",
            "consultoria economica",
            "board advisor",
            "assessor administracao",
            # 3. Docência & Explicações
            "professor economia",
            "explicador economia",
            # 4. Setor Bancário (Bancos / Banking)
            "banco controller",
            "bnp paribas controller",
            "santander controller",
            "banco diretor financeiro",
            "banco cfo",
            "banco risco",
            "corporate banking",
            "investment banking",
            "banco consultor",
            "santander finance",
            "novo banco finance",
            "bpi finance",
            "millennium bcp finance"
        ]
        all_terms = list(dict.fromkeys(core_linkedin_queries + [k for k in keywords if len(k) > 2]))

        urls_to_fetch = []
        for kw in all_terms:
            encoded_kw = urllib.parse.quote_plus(kw)
            encoded_loc = urllib.parse.quote_plus(target_loc)
            urls_to_fetch.append(
                f"{self.base_url}/jobs-guest/jobs/api/seeMoreJobPostings/search?"
                f"keywords={encoded_kw}&location={encoded_loc}&f_TPR=r{tpr_seconds}&start=0"
            )

        def _fetch(url):
            try:
                resp = self.client.get(url, timeout=6.0)
                if resp.status_code == 200:
                    return resp.text
            except Exception:
                return None
            return None

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            html_results = executor.map(_fetch, urls_to_fetch)

        for html_content in html_results:
            if not html_content:
                continue
            soup = BeautifulSoup(html_content, "html.parser")
            job_cards = soup.select("li, .base-card")

            for card in job_cards:
                title_tag = card.select_one(".base-search-card__title, h3")
                link_tag = card.select_one("a.base-card__full-link, a")
                
                if not title_tag or not link_tag or not link_tag.get("href"):
                    continue
                    
                full_url = link_tag["href"].split("?")[0] # URL limpo sem tracking params
                if full_url in seen_urls or "/jobs/view/" not in full_url:
                    continue
                seen_urls.add(full_url)
                
                title = title_tag.get_text(strip=True)
                
                comp_tag = card.select_one(".base-search-card__subtitle, h4 a, h4")
                company = comp_tag.get_text(strip=True) if comp_tag else "Confidencial"
                
                loc_tag = card.select_one(".job-search-card__location")
                loc_str = loc_tag.get_text(strip=True) if loc_tag else location
                
                time_tag = card.select_one("time")
                pub_date = now
                days_ago = 1
                if time_tag:
                    datetime_val = time_tag.get("datetime")
                    if datetime_val:
                        try:
                            pub_date = datetime.fromisoformat(datetime_val)
                            days_ago = max(0, (now - pub_date).days)
                        except Exception:
                            pass
                            
                card_text = card.get_text(" ", strip=True).lower()
                is_part_time = "part-time" in card_text or "part time" in card_text
                is_remote = "remoto" in card_text or "remote" in card_text or "hybrid" in card_text or "híbrido" in card_text

                offer_id = f"li_{re.sub(r'[^a-zA-Z0-9]', '', full_url)[-20:]}"
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
                    description=f"Vaga no LinkedIn: {title} na {company} ({loc_str})"
                ))

        return offers

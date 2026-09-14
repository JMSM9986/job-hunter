import re
import urllib.parse
from datetime import datetime, timedelta
from typing import List, Optional
from bs4 import BeautifulSoup
from .base import BaseScraper
from ..models import JobOffer

class NetEmpregosScraper(BaseScraper):
    """Scraper para o portal Net-Empregos (o maior portal de emprego em Portugal)."""
    
    def __init__(self):
        super().__init__(name="Net-Empregos", base_url="https://www.net-empregos.com")

    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Extrai data no formato DD-MM-YYYY presente no Net-Empregos."""
        date_str = date_str.strip()
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

        import concurrent.futures
        
        # 1. Preparar URLs de pesquisa para todas as palavras-chave (tipo=0 já inclui todas as ofertas, full e part-time)
        urls_to_fetch = []
        for kw in keywords:
            q_params = {"chaves": kw, "cidade": location, "categoria": 0, "zona": 1, "tipo": 0}
            encoded_params = urllib.parse.urlencode(q_params)
            urls_to_fetch.append(f"{self.base_url}/pesquisa-empregos.asp?{encoded_params}")

        # 2. Descarregamento concorrente em paralelo (8 workers)
        def _fetch(url):
            try:
                resp = self.client.get(url)
                if resp.status_code == 200:
                    try:
                        return resp.content.decode("iso-8859-1")
                    except Exception:
                        return resp.text
            except Exception:
                return None
            return None

        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            html_results = executor.map(_fetch, urls_to_fetch)

        # 3. Extração dos anúncios de cada resposta
        for html_content in html_results:
            if not html_content:
                continue
                
            soup = BeautifulSoup(html_content, "html.parser")
            job_items = soup.select(".job-item, .fl-job-item, .media")
                    
            # Se não encontrar por classe moderna, procura por linhas de tabela / links
            if not job_items:
                job_links = soup.find_all("a", href=re.compile(r'/\d+/[^/]+/$'))
                for a in job_links:
                    parent = a.find_parent("div") or a.find_parent("tr")
                    if parent and parent not in job_items:
                        job_items.append(parent)

            for item in job_items:
                # Extrair link e título
                title_el = item.find("h2") or item.find("h3") or item.find("a", href=re.compile(r'/\d+/'))
                if not title_el:
                    continue
                    
                link_tag = title_el if title_el.name == "a" else title_el.find("a")
                if not link_tag or not link_tag.get("href"):
                    continue
                    
                href = link_tag["href"]
                full_url = urllib.parse.urljoin(self.base_url, href)
                
                if full_url in seen_urls:
                    continue
                seen_urls.add(full_url)
                
                title = link_tag.get_text(strip=True)
                if not title:
                    continue

                # Extrair data de publicação
                text_content = item.get_text(" ", strip=True)
                pub_date = self._parse_date(text_content)
                if not pub_date:
                    pub_date = now
                    
                days_ago = (now - pub_date).days
                if days_ago > max_days or days_ago < 0:
                    continue

                # Extrair empresa e detalhes
                company = "Confidencial / Não especificada"
                comp_el = item.select_one(".job-company, .company, span.empresa")
                if comp_el:
                    company = comp_el.get_text(strip=True)
                else:
                    comp_match = re.search(r'Empresa:\s*([^\|\n\r]+)', text_content, re.IGNORECASE)
                    if comp_match:
                        company = comp_match.group(1).strip()

                # Identificar regime
                lower_text = text_content.lower()
                is_part_time = "part-time" in lower_text or "part time" in lower_text or "meio período" in lower_text or "avença" in lower_text or "explicador" in lower_text or "explicadores" in lower_text or "prestação de serviços" in lower_text
                is_remote = "remoto" in lower_text or "teletrabalho" in lower_text or "remote" in lower_text or "híbrido" in lower_text

                # Extrair snippet da descrição
                desc_el = item.select_one(".job-description, .description, p")
                desc = desc_el.get_text(" ", strip=True) if desc_el else text_content[:250]

                # Criar oferta
                offer_id = f"ne_{re.sub(r'[^a-zA-Z0-9]', '', full_url)[-20:]}"
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

        return offers

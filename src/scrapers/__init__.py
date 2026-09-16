from typing import List, Dict, Any
from ..models import JobOffer
from .netempregos import NetEmpregosScraper
from .sapoemprego import SapoEmpregoScraper
from .itjobs import ITJobsScraper
from .alertaemprego import AlertaEmpregoScraper
from .linkedin import LinkedInPublicScraper
from .michaelpage import MichaelPageScraper
from .hays import HaysScraper
from .expressoemprego import ExpressoEmpregoScraper

class PortalAggregator:
    """Orquestrador de pesquisa em múltiplos portais portugueses."""
    
    def __init__(self, portal_config: Dict[str, Any]):
        self.scrapers = []
        if portal_config.get("michaelpage", {}).get("enabled", True):
            self.scrapers.append(MichaelPageScraper())
        if portal_config.get("hays", {}).get("enabled", True):
            self.scrapers.append(HaysScraper())
        if portal_config.get("linkedin", {}).get("enabled", True):
            self.scrapers.append(LinkedInPublicScraper())
        if portal_config.get("expressoemprego", {}).get("enabled", True):
            self.scrapers.append(ExpressoEmpregoScraper())
        if portal_config.get("netempregos", {}).get("enabled", True):
            self.scrapers.append(NetEmpregosScraper())
        if portal_config.get("sapoemprego", {}).get("enabled", True):
            self.scrapers.append(SapoEmpregoScraper())
        if portal_config.get("itjobs", {}).get("enabled", True):
            self.scrapers.append(ITJobsScraper())
        if portal_config.get("alertaemprego", {}).get("enabled", True):
            self.scrapers.append(AlertaEmpregoScraper())

    def search_all(self, keywords: List[str], max_days: int = 15, location: str = "Lisboa") -> List[JobOffer]:
        import concurrent.futures
        from rich.console import Console
        console = Console()
        all_offers: List[JobOffer] = []
        seen_urls = set()

        def _search_scraper(scraper):
            try:
                console.print(f"  🔎 A consultar portal: [cyan]{scraper.name}[/cyan]...")
                offers = scraper.search(keywords=keywords, max_days=max_days, location=location)
                console.print(f"  ✓ Portal [cyan]{scraper.name}[/cyan]: {len(offers)} ofertas recolhidas.")
                return offers
            except Exception as e:
                console.print(f"  ⚠️ Aviso no portal [yellow]{scraper.name}[/yellow]: {e}")
                return []

        # Execução controlada com 2 workers simultâneos para não sobrecarregar recursos
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            results_list = executor.map(_search_scraper, self.scrapers)
            for results in results_list:
                for offer in results:
                    if offer.url not in seen_urls:
                        seen_urls.add(offer.url)
                        all_offers.append(offer)

        return all_offers

    def close(self):
        for s in self.scrapers:
            s.close()

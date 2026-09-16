#!/usr/bin/env python3
import os
import sys
import time

# Forçar timezone local de Portugal (Europe/Lisbon)
os.environ["TZ"] = "Europe/Lisbon"
try:
    time.tzset()
except Exception:
    pass

import argparse
from pathlib import Path
from zoneinfo import ZoneInfo
import yaml

LISBON_TZ = ZoneInfo("Europe/Lisbon")

from src.models import JobOffer
from src.cv_parser import ATSCVParser
from src.scrapers import PortalAggregator
from src.validator import JobValidator
from src.ai_matcher import AIMatcher
from src.reporter import JobReporter
from src.mailer import JobEmailNotifier
from src.cache import JobCache
from rich.console import Console

console = Console()

def load_config(config_path: str = "config.yaml") -> dict:
    p = Path(config_path)
    if not p.exists():
        return {}
    with open(p, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}

def main():
    parser = argparse.ArgumentParser(description="Agente de Procura de Emprego em Portugal baseado em CV")
    parser.add_argument("--cv", default="cv.pdf", help="Caminho para o ficheiro de CV (PDF, DOCX, TXT)")
    parser.add_argument("--days", type=int, default=15, help="Janela máxima de dias (padrão: 15)")
    parser.add_argument("--location", default="Lisboa", help="Localização de referência (padrão: Lisboa)")
    parser.add_argument("--config", default="config.yaml", help="Ficheiro de configuração")
    parser.add_argument("--email", action="store_true", default=None, help="Forçar envio de notificação por e-mail")
    parser.add_argument("--no-email", action="store_true", help="Desativar envio de e-mail nesta execução")
    parser.add_argument("--recipient", default=None, help="E-mail destinatário (padrão: jmsmonteiro@gmail.com)")
    args = parser.parse_args()

    console.print("\n[bold cyan]🚀 Inicializando Agente de Procura de Emprego (Portugal)...[/bold cyan]")
    
    # 1. Carregar Configuração
    config = load_config(args.config)
    max_days = args.days or config.get("filters", {}).get("max_days", 15)
    location = args.location
    exclude_suburbs = config.get("filters", {}).get("locations", {}).get("exclude_suburbs", [])

    # 2. Carregar e Processar CV ATS
    cv_path = Path(args.cv)
    if not cv_path.exists():
        console.print(f"[bold red]❌ Ficheiro de CV '{args.cv}' não encontrado.[/bold red]")
        sys.exit(1)

    console.print(f"📄 A analisar CV no formato ATS: [bold green]{cv_path.name}[/bold green]...")
    cv_parser = ATSCVParser(str(cv_path))
    profile = cv_parser.parse()
    
    console.print(f"👤 Candidato: [bold]{profile.name}[/bold] ({profile.professional_title})")
    console.print(f"🎖️  Associações: {', '.join(profile.certifications[:3])}")
    console.print(f"🎯 Especializações: {', '.join(profile.specializations[:2])}")
    
    # 3. Preparar Palavras-chave Canónicas (máxima cobertura com mínimo de requisições de rede)
    search_keywords = []
    for sp in config.get("search_profiles", []):
        search_keywords.extend(sp.get("keywords", []))
        
    all_keywords = list(dict.fromkeys(search_keywords)) if search_keywords else [
        "economia", "diretor financeiro", "cfo", "controller", "assessor", "explicador", "formador financas"
    ]

    console.print(f"\n🔍 Pesquisa ativa nos portais fidedignos em Portugal (últimos {max_days} dias)...")
    console.print(f"📍 Área geográfica: [bold]{location} (concelho)[/bold] e [bold]Remoto[/bold] (inclui Part-Time)")

    # 4. Executar Scrapers
    aggregator = PortalAggregator(config.get("portals", {}))
    raw_offers = aggregator.search_all(keywords=all_keywords, max_days=max_days, location=location)
    aggregator.close()

    console.print(f"📥 Total de anúncios recolhidos nos portais: [bold]{len(raw_offers)}[/bold]")

    # 5. Validação Estrita (Dias, Localização, Anúncio Ativo)
    console.print("🛡️  A validar estado ativo dos anúncios, datas de publicação e concelho de Lisboa...")
    validator = JobValidator(max_days=max_days, exclude_suburbs=exclude_suburbs)
    valid_offers = validator.filter_offers(raw_offers)
    validator.close()

    console.print(f"✅ Anúncios ativos e validados dentro dos critérios: [bold green]{len(valid_offers)}[/bold green]")

    if not valid_offers and not raw_offers:
        console.print("[bold red]⚠️ Não foi possível recolher anúncios (falha temporária de rede ou proteção de portal). Mantendo os relatórios anteriores intactos.[/bold red]")
        sys.exit(0)

    if not valid_offers:
        console.print("[yellow]⚠️ Nenhuma vaga passou todos os filtros restritos. A expandir verificação com histórico recente...[/yellow]")
        valid_offers = raw_offers[:10]

    # 6. Motor de IA e Matching com Cache Inteligente
    console.print("🧠 A calcular compatibilidade (Fit Score) com cache inteligente...")
    cache = JobCache()
    matcher = AIMatcher(profile)
    
    ranked_offers = []
    to_analyze = []
    
    for o in valid_offers:
        cached = cache.get(o.url)
        if cached:
            o.fit_score = cached.get("fit_score", 50.0)
            o.summary = cached.get("summary", o.summary)
            o.match_rationale = cached.get("match_rationale", o.match_rationale)
            o.category_fit = cached.get("category_fit", o.category_fit)
            o.matched_skills = cached.get("matched_skills", [])
            if "is_part_time" in cached:
                o.is_part_time = cached["is_part_time"]
            if "is_remote" in cached:
                o.is_remote = cached["is_remote"]
            ranked_offers.append(o)
        else:
            to_analyze.append(o)

    if to_analyze:
        newly_ranked = matcher.rank_and_process(to_analyze)
        for o in newly_ranked:
            cache.set(o.url, {
                "fit_score": o.fit_score,
                "summary": o.summary,
                "match_rationale": o.match_rationale,
                "category_fit": o.category_fit,
                "matched_skills": o.matched_skills,
                "is_part_time": o.is_part_time,
                "is_remote": o.is_remote
            })
            ranked_offers.append(o)
        cache.save()

    min_fit_score = config.get("matching", {}).get("min_fit_score", 35)
    ranked_offers = [o for o in ranked_offers if o.fit_score >= min_fit_score]
    ranked_offers.sort(key=lambda x: x.fit_score, reverse=True)

    # 7. Geração de Relatórios
    reporter = JobReporter(output_dir=".")
    
    # Consola
    reporter.print_terminal(profile, ranked_offers)
    
    # Markdown
    md_file = reporter.generate_markdown(profile, ranked_offers, filename="relatorio_vagas.md")
    console.print(f"📝 Relatório Markdown gerado em: [bold cyan]{md_file}[/bold cyan]")
    
    # HTML
    html_file = reporter.generate_html(profile, ranked_offers, filename="relatorio_vagas.html")
    console.print(f"🌐 Dashboard HTML interativo gerado em: [bold cyan]{html_file}[/bold cyan]")

    # 8. Notificação por E-mail
    email_cfg = config.get("notifications", {}).get("email", {})
    should_send_email = False
    if args.no_email:
        should_send_email = False
    elif args.email:
        should_send_email = True
    else:
        should_send_email = email_cfg.get("enabled", True)

    if should_send_email:
        recipient = args.recipient or email_cfg.get("recipient", "jmsmonteiro@gmail.com")
        sender = email_cfg.get("sender", recipient)
        top_n = email_cfg.get("top_n", 10)
        attach_report = email_cfg.get("attach_html_report", True)
        
        console.print(f"\n📬 A preparar envio do resumo diário para: [bold green]{recipient}[/bold green]...")
        notifier = JobEmailNotifier(recipient=recipient, sender=sender)
        attachment = html_file if attach_report else None
        notifier.send_daily_digest(profile, ranked_offers, html_report_path=attachment, top_n=top_n)

    console.print("\n[bold green]✨ Processo concluído com sucesso![/bold green]\n")

if __name__ == "__main__":
    main()

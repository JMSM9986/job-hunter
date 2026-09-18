from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path
from typing import List
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from .models import JobOffer, CVProfile

LISBON_TZ = ZoneInfo("Europe/Lisbon")

class JobReporter:
    """Gera relatórios em Markdown, HTML interativo e na consola terminal."""
    
    def __init__(self, output_dir: str = "."):
        self.output_dir = Path(output_dir)
        self.console = Console()

    def print_terminal(self, profile: CVProfile, offers: List[JobOffer]):
        """Apresenta um resumo executivo colorido e elegante no terminal."""
        self.console.print()
        self.console.print(Panel.fit(
            f"[bold cyan]AGENTE DE PROCURA DE EMPREGO — PORTUGAL[/bold cyan]\n"
            f"[bold]Candidato:[/bold] {profile.name} (Economista Conselheiro & OCC)\n"
            f"[bold]Filtros:[/bold] Lisboa (cidade) ou Remoto | Últimos 15 dias | Vagas Ativas | Inclui Part-Time\n"
            f"[bold]Ofertas Encontradas & Validadas:[/bold] {len(offers)}",
            border_style="cyan"
        ))

        table = Table(title="[bold green]Ofertas de Emprego Selecionadas (Ordenadas por Compatibilidade)[/bold green]", show_header=True, header_style="bold magenta")
        table.add_column("Score", style="bold yellow", width=8)
        table.add_column("Função / Empresa", style="white", width=32)
        table.add_column("Categoria", style="cyan", width=22)
        table.add_column("Regime", style="green", width=16)
        table.add_column("Data", style="blue", width=12)
        table.add_column("Portal", style="dim", width=12)
        table.add_column("Link Direto", style="underline blue", width=28)

        for o in offers[:25]: # Mostra as 25 mais compatíveis
            regime = []
            if o.is_part_time:
                regime.append("Part-Time")
            else:
                regime.append("Full-Time")
            if o.is_remote:
                regime.append("Remoto")
            else:
                regime.append("Lisboa")
            regime_str = " | ".join(regime)
            
            date_str = f"Há {o.published_days_ago}d" if o.published_days_ago > 0 else "Hoje"
            
            table.add_row(
                f"{o.fit_score}%",
                f"{o.title}\n[dim]{o.company}[/dim]",
                o.category_fit or "Geral",
                regime_str,
                date_str,
                o.source_portal,
                o.url
            )

        self.console.print(table)
        self.console.print()

    def generate_markdown(self, profile: CVProfile, offers: List[JobOffer], filename: str = "relatorio_vagas.md") -> str:
        """Gera relatório completo em Markdown estruturado."""
        filepath = self.output_dir / filename
        now_str = datetime.now(LISBON_TZ).strftime("%d/%m/%Y às %H:%M")
        
        md = []
        md.append(f"# Relatório de Oportunidades de Emprego — Portugal")
        md.append(f"**Candidato:** {profile.name}  ")
        md.append(f"**Perfil:** {profile.professional_title}  ")
        md.append(f"**Data da Pesquisa:** {now_str}  ")
        md.append(f"**Critérios:** Lisboa (concelho) ou Remoto | Anúncios ativos dos últimos 15 dias | Com ofertas em Part-Time  ")
        md.append(f"**Total de Ofertas Válidas:** {len(offers)}\n")
        
        md.append("---\n")
        md.append("## Resumo Estatístico")
        part_times = sum(1 for o in offers if o.is_part_time)
        remotes = sum(1 for o in offers if o.is_remote)
        high_fit = sum(1 for o in offers if o.fit_score >= 70)
        
        md.append(f"- **Ofertas com Elevada Compatibilidade (>= 70%):** {high_fit}")
        md.append(f"- **Ofertas em Part-Time / Prestação de Serviços:** {part_times}")
        md.append(f"- **Ofertas em Regime Remoto / Teletrabalho:** {remotes}\n")
        
        md.append("---\n")
        md.append("## Oportunidades Ordenadas por Compatibilidade (Fit Score)\n")

        for idx, o in enumerate(offers, 1):
            date_formatted = o.publication_date.strftime("%d/%m/%Y")
            regime_badges = []
            if o.is_part_time:
                regime_badges.append("`Part-Time`")
            else:
                regime_badges.append("`Full-Time`")
            if o.is_remote:
                regime_badges.append("`Remoto / Teletrabalho`")
            else:
                regime_badges.append("`Lisboa`")

            md.append(f"### {idx}. [{o.title}]({o.url}) — **Fit Score: {o.fit_score}%**")
            md.append(f"- **Empresa:** {o.company}")
            md.append(f"- **Categoria:** {o.category_fit}")
            md.append(f"- **Regime & Localização:** {' '.join(regime_badges)} ({o.location})")
            md.append(f"- **Data de Publicação:** {date_formatted} (publicado há {o.published_days_ago} dias)")
            md.append(f"- **Portal de Origem:** {o.source_portal}")
            md.append(f"- **Link Direto para Candidatura:** [{o.url}]({o.url})")
            md.append(f"- **Resumo da Oferta:** {o.summary}")
            if o.match_rationale:
                md.append(f"- **Alinhamento com o Perfil:** {o.match_rationale}")
            if o.matched_skills:
                md.append(f"- **Competências Chave Identificadas:** {', '.join(o.matched_skills)}")
            md.append("\n---\n")

        md.append("\n---\n")
        md.append("## 🏛️ Hub de Executive Search & Assessoria de Administração (Gestão de Topo)\n")
        md.append("Para um quadro superior, Economista Conselheiro e membro de órgãos sociais focado em Direção Financeira, Consultoria e Assessoria de Administração, os canais e firmas de eleição para mandatos confidenciais em Portugal são:\n")
        
        exec_firms = [
            ("LinkedIn Executive Search & Jobs", "https://www.linkedin.com/jobs/search/?keywords=CFO%20OR%20%22Diretor%20Financeiro%22%20OR%20%22Board%20Advisor%22&location=Lisbon%2C%20Portugal", "Pesquisa direta e contacto com Headhunters para cargos C-Level e de Administração em Lisboa."),
            ("Page Executive", "https://www.pageexecutive.com/", "Divisão de topo da PageGroup dedicada exclusivamente a C-Level, Conselhos de Administração e Direção Geral."),
            ("Michael Page Portugal (Finanças & Gestão)", "https://www.michaelpage.pt/jobs/finance-controlo-gestao/lisboa", "Líder em recrutamento de média e alta direção financeira e controlo de gestão."),
            ("Stanton Chase Lisboa", "https://www.stantonchase.com/office/executive-search-firm-in-lisbon-portugal", "Firma internacional de referência em Executive Search e avaliação de Boards e Administradores."),
            ("Hays Executive & Finanças", "https://www.hays.pt/", "Especialização em recrutamento de liderança financeira, banca de investimento e consultoria estratégica."),
            ("Robert Walters Portugal", "https://www.robertwalters.pt/areas-recrutamento/financas-controlo-gestao.html", "Mandatos executivos de topo nas áreas de finanças corporativas, governança e risco."),
            ("Boyden Portugal", "https://www.boyden.com/portugal/", "Uma das mais conceituadas firmas globais de Executive Search e Interim Management em Lisboa."),
            ("Amrop Portugal", "https://www.amrop.pt/", "Especialistas em liderança executiva, governança corporativa e assessoria de conselho."),
            ("GetTheJob", "https://www.getthejob.pt/", "Especialistas em outplacement executivo, assessoria de carreira e transição para órgãos de administração."),
            ("Ordem dos Economistas", "https://www.ordemeconomistas.pt/", "Bolsa de emprego e oportunidades exclusivas para Economistas Conselheiros e membros da Ordem.")
        ]
        
        for name, url, desc in exec_firms:
            md.append(f"- **[{name}]({url})**: {desc}")
            
        content = "\n".join(md)
        filepath.write_text(content, encoding="utf-8")
        return str(filepath)

    def generate_html(self, profile: CVProfile, offers: List[JobOffer], filename: str = "relatorio_vagas.html") -> str:
        """Gera dashboard web interativo em HTML moderno para abrir no browser e em qualquer dispositivo móvel."""
        filepath = self.output_dir / filename
        now_str = datetime.now(LISBON_TZ).strftime("%d/%m/%Y às %H:%M")

        # Contagens para filtros
        linkedin_count = sum(1 for o in offers if 'linkedin' in o.source_portal.lower())
        expresso_count = sum(1 for o in offers if 'expresso' in o.source_portal.lower())
        mp_count = sum(1 for o in offers if 'michael' in o.source_portal.lower())
        hays_count = sum(1 for o in offers if 'hays' in o.source_portal.lower())
        netemp_count = sum(1 for o in offers if 'net-empregos' in o.source_portal.lower() or 'netempregos' in o.source_portal.lower())
        cfo_count = sum(1 for o in offers if 'direção financeira' in (o.category_fit or '').lower() or 'cfo' in (o.category_fit or '').lower())
        admin_count = sum(1 for o in offers if 'administração' in (o.category_fit or '').lower() or 'assessoria' in (o.category_fit or '').lower())
        consult_count = sum(1 for o in offers if 'consultoria' in (o.category_fit or '').lower())
        teach_count = sum(1 for o in offers if 'professor' in (o.category_fit or '').lower() or 'explicador' in (o.category_fit or '').lower())
        pt_count = sum(1 for o in offers if o.is_part_time)
        high_fit_count = sum(1 for o in offers if o.fit_score >= 70)
        rem_count = sum(1 for o in offers if o.is_remote)

        is_banking_fn = lambda o: any(k in (o.company + " " + o.title + " " + (o.description or "") + " " + (o.summary or "")).lower() for k in [
            "banco", "banking", "banca", "santander", "bnp paribas", "natixis", "novo banco", "bpi", "millennium", "cgd", "credit risk", "capital market", "securities services", "michael page", "page executive", "hays"
        ])
        banking_count = sum(1 for o in offers if is_banking_fn(o))

        cards_html = []
        for idx, o in enumerate(offers, 1):
            badge_color = "#10b981" if o.fit_score >= 75 else ("#f59e0b" if o.fit_score >= 55 else "#6366f1")
            part_time_badge = '<span class="badge badge-part-time">⏱️ Part-Time</span>' if o.is_part_time else '<span class="badge badge-full-time">💼 Full-Time</span>'
            remote_badge = '<span class="badge badge-remote">🏠 Remoto</span>' if o.is_remote else '<span class="badge badge-location">📍 Lisboa</span>'
            
            is_banking = is_banking_fn(o)
            banking_badge = '<span class="badge" style="background: #fef9c3; color: #854d0e; font-weight: 700;">🏦 Setor Bancário</span>' if is_banking else ''

            portal_lower = o.source_portal.lower()
            if 'michael' in portal_lower:
                portal_badge = '<span class="badge" style="background: #fdf2f8; color: #be185d; font-weight: 700;">🟣 Michael Page</span>'
                portal_code = 'michaelpage'
            elif 'hays' in portal_lower:
                portal_badge = '<span class="badge" style="background: #ecfdf5; color: #047857; font-weight: 700;">🔶 Hays Portugal</span>'
                portal_code = 'hays'
            elif 'linkedin' in portal_lower:
                portal_badge = '<span class="badge" style="background: #e0f2fe; color: #0369a1; font-weight: 700;">🔵 LinkedIn Jobs</span>'
                portal_code = 'linkedin'
            elif 'expresso' in portal_lower:
                portal_badge = '<span class="badge" style="background: #fee2e2; color: #b91c1c; font-weight: 700;">🔴 Expresso Emprego</span>'
                portal_code = 'expresso'
            elif 'net-empregos' in portal_lower or 'netempregos' in portal_lower:
                portal_badge = '<span class="badge" style="background: #dcfce7; color: #15803d; font-weight: 700;">🟢 Net-Empregos</span>'
                portal_code = 'netempregos'
            else:
                portal_badge = f'<span class="badge" style="background: #f1f5f9; color: #475569; font-weight: 700;">🌐 {o.source_portal}</span>'
                portal_code = 'other'

            cat_lower = (o.category_fit or '').lower()
            if 'direção financeira' in cat_lower or 'cfo' in cat_lower:
                cat_code = 'cfo'
            elif 'administração' in cat_lower or 'assessoria' in cat_lower:
                cat_code = 'admin'
            elif 'consultoria' in cat_lower:
                cat_code = 'consulting'
            elif 'professor' in cat_lower or 'explicador' in cat_lower:
                cat_code = 'teaching'
            else:
                cat_code = 'other'

            search_blob = f"{o.title} {o.company} {o.category_fit} {o.source_portal} {' '.join(o.matched_skills)}".lower()
            skills_html = "".join([f'<span class="skill-tag">{s}</span>' for s in o.matched_skills])

            cards_html.append(f"""
            <div class="job-card" data-category="{cat_code}" data-portal="{portal_code}" data-parttime="{str(o.is_part_time).lower()}" data-remote="{str(o.is_remote).lower()}" data-banking="{str(is_banking).lower()}" data-score="{o.fit_score}" data-search="{search_blob}">
                <div class="card-header">
                    <div style="flex: 1;">
                        <div class="card-category">{o.category_fit}</div>
                        <h3 class="card-title">{o.title}</h3>
                        <div class="card-company">🏢 <strong>{o.company}</strong> • 📍 {o.location} • {portal_badge}</div>
                    </div>
                    <div class="score-box" style="background-color: {badge_color};">
                        <span class="score-num">{int(o.fit_score)}%</span>
                        <span class="score-label">Afinidade</span>
                    </div>
                </div>

                <div class="badges-row">
                    {part_time_badge}
                    {remote_badge}
                    {banking_badge}
                    <span class="badge badge-date">📅 Há {o.published_days_ago} dia(s) ({o.publication_date.strftime('%d/%m/%Y')})</span>
                </div>

                <div class="card-summary">
                    <strong>Resumo Executivo:</strong> {o.summary}
                </div>

                <div class="card-rationale">
                    💡 <em>{o.match_rationale}</em>
                </div>

                <div class="skills-row">
                    {skills_html}
                </div>

                <div class="card-footer">
                    <a href="{o.url}" target="_blank" rel="noopener noreferrer" class="btn-apply">
                        Ver Oferta no {o.source_portal} &rarr;
                    </a>
                </div>
            </div>
            """)

        cards_joined = "\n".join(cards_html)

        html_template = f"""<!DOCTYPE html>
<html lang="pt">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Centro Executivo de Oportunidades — {profile.name}</title>
    <style>
        :root {{
            --primary: #0284c7;
            --primary-dark: #0369a1;
            --bg: #f8fafc;
            --card-bg: #ffffff;
            --text-main: #0f172a;
            --text-muted: #64748b;
            --border: #e2e8f0;
            --success: #10b981;
            --warning: #f59e0b;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; }}
        body {{ background-color: var(--bg); color: var(--text-main); line-height: 1.5; padding-bottom: 60px; -webkit-font-smoothing: antialiased; }}
        
        .header {{
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0369a1 100%);
            color: white;
            padding: 32px 20px 24px 20px;
            text-align: center;
            box-shadow: 0 4px 6px -1px rgba(0,0,0,0.15);
        }}
        .header h1 {{ font-size: 1.85rem; margin-bottom: 8px; font-weight: 800; letter-spacing: -0.02em; }}
        .header p {{ font-size: 1rem; opacity: 0.92; max-width: 800px; margin: 0 auto; line-height: 1.4; }}
        .header .sub {{ font-size: 0.85rem; margin-top: 8px; opacity: 0.8; }}

        .container {{ max-width: 1100px; margin: 0 auto; padding: 20px 16px; }}

        /* Agent Control Bar */
        .agent-control-bar {{
            background: #ffffff;
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 14px 18px;
            margin-bottom: 20px;
            display: flex;
            flex-wrap: wrap;
            justify-content: space-between;
            align-items: center;
            gap: 12px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.04);
        }}
        .agent-status-group {{
            display: flex;
            align-items: center;
            gap: 10px;
            font-size: 0.9rem;
            font-weight: 600;
        }}
        .status-dot {{
            width: 10px;
            height: 10px;
            border-radius: 50%;
            background: var(--success);
            display: inline-block;
        }}
        .status-dot.pulsing {{
            background: var(--warning);
            animation: pulse 1.2s infinite;
        }}
        @keyframes pulse {{
            0% {{ transform: scale(0.95); opacity: 0.8; }}
            50% {{ transform: scale(1.25); opacity: 1; }}
            100% {{ transform: scale(0.95); opacity: 0.8; }}
        }}
        .agent-actions {{
            display: flex;
            flex-wrap: wrap;
            align-items: center;
            gap: 10px;
        }}
        .control-select {{
            padding: 8px 12px;
            border: 1px solid var(--border);
            border-radius: 8px;
            font-size: 0.88rem;
            background: #f8fafc;
            color: var(--text-main);
        }}
        .btn-action {{
            background: var(--primary);
            color: white;
            border: none;
            padding: 9px 18px;
            border-radius: 8px;
            font-size: 0.9rem;
            font-weight: 700;
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            gap: 6px;
            transition: all 0.2s;
        }}
        .btn-action:hover:not(:disabled) {{
            background: var(--primary-dark);
            transform: translateY(-1px);
        }}
        .btn-action:disabled {{
            background: #94a3b8;
            cursor: not-allowed;
            transform: none;
        }}
        .btn-secondary {{
            background: #f1f5f9;
            color: var(--text-main);
            border: 1px solid var(--border);
            padding: 9px 14px;
            border-radius: 8px;
            font-size: 0.88rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
        }}
        .btn-secondary:hover {{
            background: #e2e8f0;
        }}

        /* Console drawer */
        .console-drawer {{
            background: #090d16;
            color: #38bdf8;
            border: 1px solid #1e293b;
            border-radius: 10px;
            padding: 14px;
            font-family: 'SFMono-Regular', Consolas, Menlo, monospace;
            font-size: 0.82rem;
            max-height: 250px;
            overflow-y: auto;
            margin-bottom: 20px;
            display: none;
        }}
        .console-line {{ margin-bottom: 4px; line-height: 1.4; word-break: break-all; }}

        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 12px;
            margin-bottom: 24px;
        }}
        .stat-card {{
            background: var(--card-bg);
            padding: 16px;
            border-radius: 12px;
            border: 1px solid var(--border);
            text-align: center;
            box-shadow: 0 1px 3px rgba(0,0,0,0.03);
        }}
        .stat-card .val {{ font-size: 1.7rem; font-weight: 800; color: var(--primary); }}
        .stat-card .val.green {{ color: var(--success); }}
        .stat-card .val.orange {{ color: var(--warning); }}
        .stat-card .desc {{ color: var(--text-muted); font-size: 0.85rem; margin-top: 4px; font-weight: 500; }}

        /* Hub Box */
        .hub-box {{
            background: white;
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 24px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.03);
        }}
        .hub-box h2 {{ font-size: 1.18rem; font-weight: 700; color: #0f172a; margin-bottom: 6px; }}
        .hub-box p {{ font-size: 0.88rem; color: var(--text-muted); margin-bottom: 16px; }}
        .hub-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
            gap: 12px;
        }}
        .hub-card {{
            border: 1px solid var(--border);
            padding: 12px 14px;
            border-radius: 8px;
            background: #f8fafc;
            transition: all 0.2s;
        }}
        .hub-card:hover {{
            background: #ffffff;
            border-color: var(--primary);
            box-shadow: 0 4px 8px rgba(0,0,0,0.04);
        }}
        .hub-card-top {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px; }}
        .hub-card-top strong {{ font-size: 0.92rem; color: #0f172a; }}
        .hub-card-top a {{ font-size: 0.82rem; color: var(--primary); font-weight: 700; text-decoration: none; }}
        .hub-card p {{ font-size: 0.8rem; color: var(--text-muted); margin-bottom: 0; }}

        /* Filter Controls */
        .search-container {{
            margin-bottom: 12px;
        }}
        .search-input {{
            width: 100%;
            padding: 12px 16px;
            border-radius: 10px;
            border: 1px solid var(--border);
            font-size: 0.95rem;
            background: #ffffff;
            outline: none;
            box-shadow: 0 1px 2px rgba(0,0,0,0.03);
            transition: border 0.2s;
        }}
        .search-input:focus {{
            border-color: var(--primary);
            box-shadow: 0 0 0 3px rgba(2, 132, 199, 0.15);
        }}

        .filter-bar {{
            background: white;
            padding: 14px 16px;
            border-radius: 12px;
            border: 1px solid var(--border);
            margin-bottom: 24px;
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            align-items: center;
        }}
        .filter-btn {{
            padding: 7px 14px;
            border-radius: 20px;
            border: 1px solid var(--border);
            background: #f8fafc;
            cursor: pointer;
            font-size: 0.84rem;
            font-weight: 600;
            color: var(--text-main);
            transition: all 0.15s;
            display: inline-flex;
            align-items: center;
            gap: 6px;
        }}
        .filter-btn .count {{
            background: rgba(0,0,0,0.07);
            padding: 1px 6px;
            border-radius: 10px;
            font-size: 0.76rem;
        }}
        .filter-btn.active {{
            background: var(--primary);
            color: white;
            border-color: var(--primary);
        }}
        .filter-btn.active .count {{
            background: rgba(255,255,255,0.25);
            color: white;
        }}
        .filter-btn:hover:not(.active) {{
            background: #e2e8f0;
        }}

        /* Job Cards */
        .job-card {{
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 14px;
            padding: 22px;
            margin-bottom: 18px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.03);
            transition: transform 0.2s, box-shadow 0.2s;
        }}
        .job-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 8px 16px rgba(0,0,0,0.06);
        }}
        .card-header {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            gap: 14px;
            margin-bottom: 12px;
        }}
        .card-category {{
            font-size: 0.78rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: var(--primary);
            font-weight: 800;
            margin-bottom: 4px;
        }}
        .card-title {{
            font-size: 1.25rem;
            font-weight: 700;
            color: #0f172a;
            line-height: 1.3;
        }}
        .card-company {{
            color: var(--text-muted);
            font-size: 0.92rem;
            margin-top: 6px;
            display: flex;
            flex-wrap: wrap;
            align-items: center;
            gap: 6px;
        }}
        .score-box {{
            padding: 8px 12px;
            border-radius: 10px;
            color: white;
            text-align: center;
            min-width: 80px;
            flex-shrink: 0;
        }}
        .score-num {{ font-size: 1.25rem; font-weight: 800; display: block; }}
        .score-label {{ font-size: 0.68rem; text-transform: uppercase; opacity: 0.9; font-weight: 700; }}

        .badges-row {{ display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 14px; }}
        .badge {{
            padding: 4px 10px;
            border-radius: 6px;
            font-size: 0.8rem;
            font-weight: 600;
            display: inline-flex;
            align-items: center;
        }}
        .badge-part-time {{ background: #fef3c7; color: #92400e; }}
        .badge-full-time {{ background: #e0f2fe; color: #0369a1; }}
        .badge-remote {{ background: #dcfce7; color: #166534; }}
        .badge-location {{ background: #f1f5f9; color: #475569; }}
        .badge-date {{ background: #f3e8ff; color: #6b21a8; }}

        .card-summary {{ font-size: 0.94rem; color: #334155; margin-bottom: 10px; line-height: 1.5; }}
        .card-rationale {{ font-size: 0.88rem; color: #065f46; background: #ecfdf5; border-left: 3px solid #10b981; padding: 10px 14px; border-radius: 4px 8px 8px 4px; margin-bottom: 14px; line-height: 1.45; }}

        .skills-row {{ display: flex; gap: 6px; flex-wrap: wrap; margin-bottom: 16px; }}
        .skill-tag {{
            background: #f1f5f9;
            color: #334155;
            font-size: 0.76rem;
            padding: 3px 8px;
            border-radius: 4px;
            font-weight: 600;
        }}

        .card-footer {{ display: flex; justify-content: flex-end; }}
        .btn-apply {{
            display: inline-block;
            background: var(--primary);
            color: white;
            padding: 10px 20px;
            border-radius: 8px;
            text-decoration: none;
            font-weight: 700;
            font-size: 0.9rem;
            transition: all 0.2s;
        }}
        .btn-apply:hover {{ background: var(--primary-dark); transform: translateY(-1px); }}

        .empty-state {{
            background: white;
            border: 1px dashed var(--border);
            border-radius: 12px;
            padding: 40px 20px;
            text-align: center;
            color: var(--text-muted);
            display: none;
        }}
    </style>
</head>
<body>

<div class="header">
    <h1>🎯 Centro de Oportunidades Executivas — Portugal</h1>
    <p>Pesquisa estruturada para <strong>{profile.name}</strong> • Economista Conselheiro & Membro da OCC</p>
    <div class="sub">Áreas Exclusivas: Direção Financeira (CFO), Assessoria de Administração, Consultoria Económica, Docência & Explicações</div>
</div>

<div class="container">

    <!-- Agent Control Bar -->
    <div class="agent-control-bar">
        <div class="agent-status-group">
            <span class="status-dot" id="agentDot"></span>
            <span id="agentStatusText">Agente Operacional • Última atualização: {now_str}</span>
        </div>
        <div class="agent-actions">
            <select id="daysSelect" class="control-select">
                <option value="15" selected>Últimos 15 dias</option>
                <option value="7">Últimos 7 dias</option>
                <option value="30">Últimos 30 dias</option>
            </select>
            <button id="btnRun" class="btn-action" onclick="triggerRun()">
                <span id="btnIcon">🚀</span>
                <span id="btnText">Atualizar Pesquisa</span>
            </button>
            <button class="btn-secondary" onclick="copyExecutiveSummary()" id="btnCopySummary" title="Copiar resumo para WhatsApp ou Notas">
                📋 Copiar Resumo
            </button>
            <a href="/resumo.txt" target="_blank" class="btn-secondary" style="text-decoration: none; display: inline-flex; align-items: center;" title="Ver resumo em texto simples">
                📄 Texto
            </a>
            <button class="btn-secondary" onclick="toggleConsole()">
                📟 Logs
            </button>
        </div>
    </div>

    <!-- Live Console Drawer -->
    <div class="console-drawer" id="consoleDrawer">
        <div style="display: flex; justify-content: space-between; border-bottom: 1px solid #334155; padding-bottom: 6px; margin-bottom: 8px;">
            <span style="font-weight: 700; color: #ffffff;">📟 Consola de Execução em Tempo Real</span>
            <span style="color: #94a3b8; cursor: pointer;" onclick="toggleConsole()">✕ Fechar</span>
        </div>
        <div id="consoleBody">Aguardando execução...</div>
    </div>

    <!-- KPI Stats Grid -->
    <div class="stats-grid">
        <div class="stat-card">
            <div class="val" id="kpiTotal">{len(offers)}</div>
            <div class="desc">Vagas Ativas & Validadas</div>
        </div>
        <div class="stat-card">
            <div class="val green" id="kpiHigh">{high_fit_count}</div>
            <div class="desc">Alta Afinidade (&ge; 70%)</div>
        </div>
        <div class="stat-card">
            <div class="val orange" id="kpiPt">{pt_count}</div>
            <div class="desc">Ofertas em Part-Time</div>
        </div>
        <div class="stat-card">
            <div class="val" style="color: #0369a1;" id="kpiPortals">5 Portais</div>
            <div class="desc">Michael Page, Hays, LinkedIn, Expresso, Net-Emp.</div>
        </div>
    </div>

    <!-- Hub de Executive Search & Assessoria de Administração -->
    <div class="hub-box">
        <h2>🏛️ Hub de Executive Search & Assessoria de Administração (Gestão de Topo)</h2>
        <p>Canais e consultoras de referência para mandatos confidenciais de C-Level, Direção Financeira e Conselhos em Lisboa:</p>
        <div class="hub-grid">
            <div class="hub-card" style="border-color: #0284c7; background: #f0f9ff;">
                <div class="hub-card-top">
                    <strong style="color: #0369a1;">LinkedIn Executive Search</strong>
                    <a href="https://www.linkedin.com/jobs/search/?keywords=CFO%20OR%20%22Diretor%20Financeiro%22%20OR%20%22Board%20Advisor%22&location=Lisbon%2C%20Portugal" target="_blank" rel="noopener noreferrer">Pesquisar &rarr;</a>
                </div>
                <p>Contacto direto com Headhunters para cargos C-Level e Administração em Lisboa.</p>
            </div>
            <div class="hub-card">
                <div class="hub-card-top">
                    <strong>Page Executive</strong>
                    <a href="https://www.pageexecutive.com/" target="_blank" rel="noopener noreferrer">Aceder &rarr;</a>
                </div>
                <p>Divisão dedicada a C-Level, Administração e Direção Geral em Portugal.</p>
            </div>
            <div class="hub-card">
                <div class="hub-card-top">
                    <strong>Michael Page Portugal</strong>
                    <a href="https://www.michaelpage.pt/jobs/finance-controlo-gestao/lisboa" target="_blank" rel="noopener noreferrer">Aceder &rarr;</a>
                </div>
                <p>Recrutamento qualificado de Direção Financeira, FP&A e Corporate Finance.</p>
            </div>
            <div class="hub-card">
                <div class="hub-card-top">
                    <strong>Stanton Chase Lisboa</strong>
                    <a href="https://www.stantonchase.com/office/executive-search-firm-in-lisbon-portugal" target="_blank" rel="noopener noreferrer">Aceder &rarr;</a>
                </div>
                <p>Executive Search global para Administradores, Board e Direção-Geral.</p>
            </div>
            <div class="hub-card">
                <div class="hub-card-top">
                    <strong>Hays Executive & Finanças</strong>
                    <a href="https://www.hays.pt/" target="_blank" rel="noopener noreferrer">Aceder &rarr;</a>
                </div>
                <p>Liderança executiva para Banca, Seguros, Finanças e Consultoria.</p>
            </div>
            <div class="hub-card">
                <div class="hub-card-top">
                    <strong>Robert Walters Portugal</strong>
                    <a href="https://www.robertwalters.pt/areas-recrutamento/financas-controlo-gestao.html" target="_blank" rel="noopener noreferrer">Aceder &rarr;</a>
                </div>
                <p>Quadros executivos nas áreas financeira, risco e governança corporativa.</p>
            </div>
            <div class="hub-card">
                <div class="hub-card-top">
                    <strong>Boyden Portugal</strong>
                    <a href="https://www.boyden.com/portugal/" target="_blank" rel="noopener noreferrer">Aceder &rarr;</a>
                </div>
                <p>Executive Search internacional de topo e Interim Management em Lisboa.</p>
            </div>
            <div class="hub-card">
                <div class="hub-card-top">
                    <strong>Amrop Portugal</strong>
                    <a href="https://www.amrop.pt/" target="_blank" rel="noopener noreferrer">Aceder &rarr;</a>
                </div>
                <p>Especialistas em avaliação de Conselhos de Administração e governança.</p>
            </div>
            <div class="hub-card">
                <div class="hub-card-top">
                    <strong>GetTheJob</strong>
                    <a href="https://www.getthejob.pt/" target="_blank" rel="noopener noreferrer">Aceder &rarr;</a>
                </div>
                <p>Transição de carreira, assessoria executiva e posicionamento estratégico.</p>
            </div>
            <div class="hub-card">
                <div class="hub-card-top">
                    <strong>Ordem dos Economistas</strong>
                    <a href="https://www.ordemeconomistas.pt/" target="_blank" rel="noopener noreferrer">Aceder &rarr;</a>
                </div>
                <p>Bolsa de oportunidades e rede profissional de Economistas Conselheiros.</p>
            </div>
        </div>
    </div>

    <!-- Live Search -->
    <div class="search-container">
        <input type="text" id="searchInput" class="search-input" placeholder="🔍 Filtrar vagas por cargo, empresa, portal ou competência em tempo real..." oninput="applyFilters()">
    </div>

    <!-- Filter Buttons -->
    <div class="filter-bar">
        <span style="font-weight: 700; font-size: 0.88rem; margin-right: 4px; color: var(--text-muted);">Portais:</span>
        <button class="filter-btn active" data-filter-type="portal" data-filter-val="all" onclick="setFilter(this)">Todas <span class="count">{len(offers)}</span></button>
        <button class="filter-btn" data-filter-type="portal" data-filter-val="michaelpage" onclick="setFilter(this)">🟣 Michael Page <span class="count">{mp_count}</span></button>
        <button class="filter-btn" data-filter-type="portal" data-filter-val="hays" onclick="setFilter(this)">🔶 Hays <span class="count">{hays_count}</span></button>
        <button class="filter-btn" data-filter-type="portal" data-filter-val="linkedin" onclick="setFilter(this)">🔵 LinkedIn <span class="count">{linkedin_count}</span></button>
        <button class="filter-btn" data-filter-type="portal" data-filter-val="expresso" onclick="setFilter(this)">🔴 Expresso Emprego <span class="count">{expresso_count}</span></button>
        <button class="filter-btn" data-filter-type="portal" data-filter-val="netempregos" onclick="setFilter(this)">🟢 Net-Empregos <span class="count">{netemp_count}</span></button>

        <span style="font-weight: 700; font-size: 0.88rem; margin-left: 8px; margin-right: 4px; color: var(--text-muted);">Áreas:</span>
        <button class="filter-btn" data-filter-type="cat" data-filter-val="cfo" onclick="setFilter(this)">💼 CFO / Dir. Financeira <span class="count">{cfo_count}</span></button>
        <button class="filter-btn" data-filter-type="cat" data-filter-val="admin" onclick="setFilter(this)">🏛️ Assessoria Admin <span class="count">{admin_count}</span></button>
        <button class="filter-btn" data-filter-type="cat" data-filter-val="consulting" onclick="setFilter(this)">📈 Consultoria <span class="count">{consult_count}</span></button>
        <button class="filter-btn" data-filter-type="cat" data-filter-val="teaching" onclick="setFilter(this)">🎓 Ensino / Explicações <span class="count">{teach_count}</span></button>

        <span style="font-weight: 700; font-size: 0.88rem; margin-left: 8px; margin-right: 4px; color: var(--text-muted);">Critérios:</span>
        <button class="filter-btn" data-filter-type="spec" data-filter-val="banking" onclick="setFilter(this)">🏦 Bancos & Finanças <span class="count">{banking_count}</span></button>
        <button class="filter-btn" data-filter-type="spec" data-filter-val="high" onclick="setFilter(this)">⭐ Score &ge; 70% <span class="count">{high_fit_count}</span></button>
        <button class="filter-btn" data-filter-type="spec" data-filter-val="pt" onclick="setFilter(this)">⏱️ Part-Time <span class="count">{pt_count}</span></button>
    </div>

    <!-- Job Offer Cards List (ZERO IFRAMES) -->
    <div id="jobList">
        {cards_joined}
    </div>

    <div id="emptyState" class="empty-state">
        <h3>Nenhuma vaga corresponde aos filtros selecionados.</h3>
        <p style="margin-top: 6px;">Tente limpar a pesquisa de texto ou selecionar "Todas".</p>
    </div>
</div>

<script>
let currentFilterType = 'portal';
let currentFilterVal = 'all';
let isRunning = false;

function setFilter(btn) {{
    document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    currentFilterType = btn.getAttribute('data-filter-type');
    currentFilterVal = btn.getAttribute('data-filter-val');
    applyFilters();
}}

function applyFilters() {{
    const query = (document.getElementById('searchInput').value || '').toLowerCase().trim();
    const cards = document.querySelectorAll('.job-card');
    let visibleCount = 0;

    cards.forEach(card => {{
        const portal = card.getAttribute('data-portal');
        const category = card.getAttribute('data-category');
        const isPt = card.getAttribute('data-parttime') === 'true';
        const isBanking = card.getAttribute('data-banking') === 'true';
        const score = parseFloat(card.getAttribute('data-score')) || 0;
        const searchBlob = card.getAttribute('data-search') || '';

        // Critério do botão
        let matchesFilter = false;
        if (currentFilterType === 'portal') {{
            matchesFilter = (currentFilterVal === 'all') || (portal === currentFilterVal);
        }} else if (currentFilterType === 'cat') {{
            matchesFilter = (category === currentFilterVal);
        }} else if (currentFilterType === 'spec') {{
            if (currentFilterVal === 'high') matchesFilter = (score >= 70);
            if (currentFilterVal === 'pt') matchesFilter = isPt;
            if (currentFilterVal === 'banking') matchesFilter = isBanking;
        }}

        // Critério de pesquisa de texto
        let matchesSearch = true;
        if (query.length > 0) {{
            matchesSearch = searchBlob.includes(query);
        }}

        if (matchesFilter && matchesSearch) {{
            card.style.display = 'block';
            visibleCount++;
        }} else {{
            card.style.display = 'none';
        }}
    }});

    const empty = document.getElementById('emptyState');
    if (empty) {{
        empty.style.display = (visibleCount === 0) ? 'block' : 'none';
    }}
}}

function toggleConsole() {{
    const el = document.getElementById('consoleDrawer');
    if (el) {{
        el.style.display = (el.style.display === 'none' || el.style.display === '') ? 'block' : 'none';
    }}
}}

const pageRunTimestamp = "{now_str}";

async function copyExecutiveSummary() {{
    try {{
        const res = await fetch('/resumo.txt');
        if (!res.ok) throw new Error('Não disponível');
        const txt = await res.text();
        await navigator.clipboard.writeText(txt);
        const btn = document.getElementById('btnCopySummary');
        if (btn) {{
            const orig = btn.innerHTML;
            btn.innerHTML = '✅ Copiado!';
            setTimeout(() => {{ btn.innerHTML = orig; }}, 2500);
        }}
    }} catch (e) {{
        window.open('/resumo.txt', '_blank');
    }}
}}

// Polling e controlo do agente com a API local
async function pollAgentStatus() {{
    try {{
        const res = await fetch('/api/status');
        if (!res.ok) return;
        const data = await res.json();

        const dot = document.getElementById('agentDot');
        const statusText = document.getElementById('agentStatusText');
        const btnRun = document.getElementById('btnRun');
        const btnText = document.getElementById('btnText');
        const btnIcon = document.getElementById('btnIcon');

        if (data.is_running) {{
            isRunning = true;
            if (dot) dot.className = 'status-dot pulsing';
            if (statusText) statusText.textContent = 'Agente a Pesquisar Portais em Tempo Real...';
            if (btnRun) btnRun.disabled = true;
            if (btnText) btnText.textContent = 'A Pesquisar...';
            if (btnIcon) btnIcon.textContent = '⏳';
        }} else {{
            if (isRunning) {{
                // Terminou a execução agora - recarregar com cache-busting obrigatório no telemóvel
                isRunning = false;
                window.location.href = window.location.pathname + '?v=' + Date.now();
                return;
            }}
            // Detetar atualização externa (ex: agendamento matinal autónomo das 09:00)
            if (data.last_run && data.last_run !== pageRunTimestamp) {{
                window.location.href = window.location.pathname + '?v=' + Date.now();
                return;
            }}
            if (dot) dot.className = 'status-dot';
            if (statusText) statusText.textContent = data.last_run ? ('Agente Operacional • Atualizado em ' + data.last_run) : 'Agente Operacional';
            if (btnRun) btnRun.disabled = false;
            if (btnText) btnText.textContent = 'Atualizar Pesquisa';
            if (btnIcon) btnIcon.textContent = '🚀';
        }}

        if (data.logs && data.logs.length > 0) {{
            const consoleBody = document.getElementById('consoleBody');
            if (consoleBody) {{
                consoleBody.innerHTML = data.logs.map(l => `<div class="console-line">${{l}}</div>`).join('');
                consoleBody.scrollTop = consoleBody.scrollHeight;
            }}
        }}

    }} catch (e) {{
        // Modo offline ou sem servidor local
    }}
}}

async function triggerRun() {{
    const days = document.getElementById('daysSelect').value;
    const btnRun = document.getElementById('btnRun');
    const btnText = document.getElementById('btnText');
    const btnIcon = document.getElementById('btnIcon');
    const statusText = document.getElementById('agentStatusText');
    const dot = document.getElementById('agentDot');

    if (btnRun) btnRun.disabled = true;
    if (btnText) btnText.textContent = 'A Iniciar...';
    if (btnIcon) btnIcon.textContent = '⏳';
    if (statusText) statusText.textContent = 'Agente a Iniciar Pesquisa nos Portais...';
    if (dot) dot.className = 'status-dot pulsing';
    isRunning = true;

    // Abrir consola para feedback imediato
    const consoleDrawer = document.getElementById('consoleDrawer');
    if (consoleDrawer) consoleDrawer.style.display = 'block';

    try {{
        const res = await fetch('/api/run', {{
            method: 'POST',
            headers: {{ 'Content-Type': 'application/json' }},
            body: JSON.stringify({{ days: parseInt(days), send_email: true }})
        }});
        const data = await res.json();
        setTimeout(pollAgentStatus, 400);
    }} catch (err) {{
        alert('Erro ao comunicar com o agente: ' + err);
        if (btnRun) btnRun.disabled = false;
        if (btnText) btnText.textContent = 'Atualizar Pesquisa';
        if (btnIcon) btnIcon.textContent = '🚀';
        isRunning = false;
    }}
}}

// Iniciar polling a cada 2.5s
setInterval(pollAgentStatus, 2500);
pollAgentStatus();
</script>

</body>
</html>"""
        
        filepath.write_text(html_template, encoding="utf-8")
        return str(filepath)


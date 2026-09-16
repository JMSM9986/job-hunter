import os
import subprocess
import smtplib
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path
from typing import List, Optional
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from .models import JobOffer, CVProfile
from rich.console import Console

console = Console()
LISBON_TZ = ZoneInfo("Europe/Lisbon")

class JobEmailNotifier:
    """
    Envia o resumo executivo diário de vagas de emprego por e-mail.
    Suporta:
    1. macOS Apple Mail nativo (via osascript) - zero configuração de senhas se a conta já estiver no Mac.
    2. SMTP padrão (Gmail TLS/SSL) se credenciais SMTP forem configuradas no .env ou Render.
    """

    def __init__(self, recipient: str = "jmsmonteiro@gmail.com", sender: Optional[str] = None):
        self.recipient = recipient
        self.sender = sender or recipient
        self.smtp_host = os.environ.get("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = int(os.environ.get("SMTP_PORT", "587"))
        self.smtp_user = os.environ.get("SMTP_USER", self.sender)
        self.smtp_password = os.environ.get("SMTP_PASSWORD") or os.environ.get("GMAIL_APP_PASSWORD")

    def _get_public_url(self) -> str:
        pub_file = Path(__file__).resolve().parent.parent / "public_url.txt"
        if pub_file.exists():
            url = pub_file.read_text(encoding="utf-8").strip()
            if url.startswith("http"):
                return url
        return "https://job-hunter-agent-e9z0.onrender.com"

    def build_text_body(self, profile: CVProfile, offers: List[JobOffer], top_n: int = 10) -> str:
        """Constrói o corpo executivo em texto simples estruturado para Apple Mail."""
        now_str = datetime.now(LISBON_TZ).strftime("%d/%m/%Y às %H:%M")
        pub_url = self._get_public_url()
        
        part_times = sum(1 for o in offers if o.is_part_time)
        remotes = sum(1 for o in offers if o.is_remote)
        high_fit = sum(1 for o in offers if o.fit_score >= 70)

        lines = [
            f"🎯 RESUMO EXECUTIVO DIÁRIO — OPORTUNIDADES DE EMPREGO (PORTUGAL)",
            f"=" * 70,
            f"Candidato: {profile.name} ({profile.professional_title})",
            f"Data da Pesquisa: {now_str}",
            f"Critérios: Lisboa (concelho) ou Remoto | Últimos 15 dias | Vagas Ativas | Inclui Part-Time",
            f"Total de Ofertas Válidas Encontradas: {len(offers)}",
            "",
            f"📱 LINK DO DASHBOARD NO TELEMÓVEL (4G/5G): {pub_url}",
            f"🏠 LINK PERMANENTE (Mesmo Wi-Fi): http://192.168.1.245:5050",
            "",
            f"📊 INDICADORES DO DIA:",
            f"• Elevada Afinidade (Fit Score >= 70%): {high_fit} ofertas",
            f"• Regime Part-Time / Prestação de Serviços: {part_times} ofertas",
            f"• Regime Remoto / Teletrabalho: {remotes} ofertas",
            "",
            f"🌟 TOP {min(top_n, len(offers))} OPORTUNIDADES MAIS COMPATÍVEIS:",
            f"-" * 70,
        ]

        for idx, o in enumerate(offers[:top_n], 1):
            regime = "Part-Time" if o.is_part_time else "Full-Time"
            location = "Remoto" if o.is_remote else o.location
            date_str = f"Há {o.published_days_ago} dias ({o.publication_date.strftime('%d/%m/%Y')})" if o.published_days_ago > 0 else "Hoje"
            
            lines.append(f"[{idx}] {o.title} — Compatibilidade: {o.fit_score}%")
            lines.append(f"    🏢 Empresa: {o.company} | Categoria: {o.category_fit or 'Geral'}")
            lines.append(f"    📍 Regime: {regime} • {location} | 📅 Publicação: {date_str}")
            lines.append(f"    🌐 Portal: {o.source_portal}")
            lines.append(f"    🔗 Candidatura Direta: {o.url}")
            lines.append(f"    📝 Resumo: {o.summary}")
            if o.match_rationale:
                lines.append(f"    🎯 Alinhamento: {o.match_rationale}")
            if o.matched_skills:
                lines.append(f"    🔑 Competências: {', '.join(o.matched_skills)}")
            lines.append("")

        lines.extend([
            f"-" * 70,
            f"🏛️ HUB DE EXECUTIVE SEARCH & RECRUTAMENTO DE TOPO (PORTUGAL):",
            f"Para mandatos confidenciais de Direção, Board Advisory e Gestão de Topo:",
            f"• Michael Page Portugal: https://www.michaelpage.pt/",
            f"• Page Executive (C-Level & Board): https://www.pageexecutive.com/",
            f"• Hays Portugal (Executivo & Finanças): https://www.hays.pt/",
            f"• Stanton Chase Lisboa (Executive Search): https://www.stantonchase.com/office/executive-search-firm-in-lisbon-portugal",
            f"• Robert Walters Portugal: https://www.robertwalters.pt/",
            f"• GetTheJob (Outplacement Executivo): https://www.getthejob.pt/",
            "",
            f"📌 O relatório completo e interativo em HTML segue em anexo a esta mensagem.",
            f"Pode abri-lo diretamente no seu browser para filtrar por Part-Time, Remoto ou Categoria.",
            "",
            f"Gerado automaticamente pelo Agente Autónomo de Procura de Emprego Antigravity.",
            f"Próxima atualização programada: amanhã às 09:00."
        ])

        return "\n".join(lines)

    def build_html_body(self, profile: CVProfile, offers: List[JobOffer], top_n: int = 10) -> str:
        """Constrói um e-mail em HTML responsivo e com design executivo moderno."""
        pub_url = self._get_public_url()
        part_times = sum(1 for o in offers if o.is_part_time)
        remotes = sum(1 for o in offers if o.is_remote)
        high_fit = sum(1 for o in offers if o.fit_score >= 70)

        rows = []
        for idx, o in enumerate(offers[:top_n], 1):
            score_color = "#10b981" if o.fit_score >= 75 else ("#f59e0b" if o.fit_score >= 55 else "#6366f1")
            part_time_badge = '<span style="background:#fef3c7;color:#92400e;padding:3px 8px;border-radius:12px;font-size:11px;font-weight:bold;">Part-Time</span>' if o.is_part_time else '<span style="background:#e0e7ff;color:#3730a3;padding:3px 8px;border-radius:12px;font-size:11px;font-weight:bold;">Full-Time</span>'
            remote_badge = '<span style="background:#d1fae5;color:#065f46;padding:3px 8px;border-radius:12px;font-size:11px;font-weight:bold;">Remoto</span>' if o.is_remote else f'<span style="background:#f1f5f9;color:#475569;padding:3px 8px;border-radius:12px;font-size:11px;font-weight:bold;">{o.location}</span>'
            
            rows.append(f"""
            <div style="background:#ffffff;border:1px solid #e2e8f0;border-radius:8px;padding:16px;margin-bottom:14px;box-shadow:0 1px 3px rgba(0,0,0,0.05);">
                <table style="width:100%;border-collapse:collapse;">
                    <tr>
                        <td style="vertical-align:top;">
                            <div style="font-size:11px;font-weight:bold;text-transform:uppercase;color:#6366f1;letter-spacing:0.5px;">{o.category_fit or 'Geral'}</div>
                            <h3 style="margin:4px 0 6px 0;font-size:16px;color:#0f172a;"><a href="{o.url}" style="color:#0f172a;text-decoration:none;" target="_blank">{idx}. {o.title}</a></h3>
                            <div style="font-size:13px;color:#64748b;margin-bottom:8px;">
                                🏢 <strong>{o.company}</strong> &nbsp;•&nbsp; 📍 {o.location} &nbsp;•&nbsp; 🌐 {o.source_portal}
                            </div>
                        </td>
                        <td style="width:80px;text-align:right;vertical-align:top;">
                            <div style="background:{score_color};color:#ffffff;font-size:15px;font-weight:bold;padding:6px 10px;border-radius:8px;display:inline-block;text-align:center;">
                                {int(o.fit_score)}%
                            </div>
                            <div style="font-size:10px;color:#64748b;margin-top:2px;">Fit Score</div>
                        </td>
                    </tr>
                </table>

                <div style="margin-bottom:10px;">
                    {part_time_badge} &nbsp; {remote_badge} &nbsp;
                    <span style="font-size:11px;color:#64748b;">Publicado: {o.publication_date.strftime('%d/%m/%Y')} (há {o.published_days_ago} dias)</span>
                </div>

                <p style="font-size:13px;color:#334155;line-height:1.5;margin:8px 0;background:#f8fafc;padding:10px;border-radius:6px;">
                    <strong>Resumo:</strong> {o.summary}
                </p>

                {f'<p style="font-size:12px;color:#0369a1;margin:4px 0;">🎯 <strong>Alinhamento:</strong> {o.match_rationale}</p>' if o.match_rationale else ''}

                <div style="margin-top:12px;text-align:right;">
                    <a href="{o.url}" style="background:#0284c7;color:#ffffff;text-decoration:none;padding:8px 16px;border-radius:6px;font-size:12px;font-weight:bold;display:inline-block;" target="_blank">
                        Ver Anúncio e Candidatar &rarr;
                    </a>
                </div>
            </div>
            """)

        cards_html = "\n".join(rows)

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Resumo Diário de Vagas Executivas</title>
        </head>
        <body style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;background-color:#f1f5f9;margin:0;padding:20px;color:#0f172a;">
            <div style="max-width:680px;margin:0 auto;background:#ffffff;border-radius:12px;overflow:hidden;box-shadow:0 4px 6px -1px rgba(0,0,0,0.1);">
                <!-- Header -->
                <div style="background:linear-gradient(135deg, #0f172a 0%, #1e293b 100%);color:#ffffff;padding:28px 24px;border-bottom:3px solid #0284c7;">
                    <div style="font-size:12px;text-transform:uppercase;letter-spacing:1px;color:#38bdf8;font-weight:bold;">Agente Autónomo de Emprego • Notificação Matinal</div>
                    <h1 style="margin:8px 0 4px 0;font-size:22px;color:#ffffff;">Resumo Diário de Vagas Executivas</h1>
                    <p style="margin:0;font-size:14px;color:#94a3b8;">Candidato: <strong>{profile.name}</strong> ({profile.professional_title})</p>
                    <p style="margin:4px 0 0 0;font-size:12px;color:#64748b;">Pesquisa em Lisboa (concelho) & Remoto • Anúncios ativos nos últimos 15 dias • Inclui Part-Time</p>
                </div>

                <!-- Link Telemóvel / Dashboard -->
                <div style="background:#0284c7;padding:12px 20px;text-align:center;">
                    <a href="{pub_url}" style="background:#ffffff;color:#0284c7;text-decoration:none;font-weight:bold;font-size:14px;padding:9px 20px;border-radius:6px;display:inline-block;box-shadow:0 2px 4px rgba(0,0,0,0.15);" target="_blank">
                        📱 Abrir Dashboard no Telemóvel (4G/5G) &rarr;
                    </a>
                    <div style="font-size:11px;color:#e0f2fe;margin-top:6px;">Em casa/escritório (Mesmo Wi-Fi): <a href="http://192.168.1.245:5050" style="color:#ffffff;font-weight:bold;text-decoration:underline;">http://192.168.1.245:5050</a></div>
                </div>

                <!-- KPI Bar -->
                <div style="background:#f8fafc;padding:14px 24px;border-bottom:1px solid #e2e8f0;">
                    <table style="width:100%;text-align:center;border-collapse:collapse;">
                        <tr>
                            <td style="border-right:1px solid #e2e8f0;padding:4px;">
                                <div style="font-size:20px;font-weight:bold;color:#0f172a;">{len(offers)}</div>
                                <div style="font-size:11px;color:#64748b;">Vagas Validadas</div>
                            </td>
                            <td style="border-right:1px solid #e2e8f0;padding:4px;">
                                <div style="font-size:20px;font-weight:bold;color:#10b981;">{high_fit}</div>
                                <div style="font-size:11px;color:#64748b;">Fit Score &ge; 70%</div>
                            </td>
                            <td style="border-right:1px solid #e2e8f0;padding:4px;">
                                <div style="font-size:20px;font-weight:bold;color:#d97706;">{part_times}</div>
                                <div style="font-size:11px;color:#64748b;">Part-Time / Avença</div>
                            </td>
                            <td style="padding:4px;">
                                <div style="font-size:20px;font-weight:bold;color:#6366f1;">{remotes}</div>
                                <div style="font-size:11px;color:#64748b;">Remoto / Teletrabalho</div>
                            </td>
                        </tr>
                    </table>
                </div>

                <!-- Main Content -->
                <div style="padding:24px;">
                    <h2 style="font-size:16px;color:#0f172a;margin-top:0;margin-bottom:16px;border-bottom:2px solid #e2e8f0;padding-bottom:8px;">
                        🌟 Top {min(top_n, len(offers))} Oportunidades Selecionadas por Compatibilidade
                    </h2>
                    {cards_html}

                    <!-- Hub Executivo -->
                    <div style="background:#f8fafc;border:1px solid #cbd5e1;border-radius:8px;padding:16px;margin-top:24px;">
                        <h3 style="margin:0 0 10px 0;font-size:14px;color:#0f172a;">🏛️ Hub de Executive Search & Gestão de Topo</h3>
                        <p style="font-size:12px;color:#64748b;margin:0 0 12px 0;">Consultoras especializadas para candidaturas espontâneas e mandatos executivos confidenciais:</p>
                        <table style="width:100%;font-size:12px;border-collapse:collapse;">
                            <tr>
                                <td style="padding:4px 0;"><a href="https://www.michaelpage.pt/" style="color:#0284c7;text-decoration:none;font-weight:bold;" target="_blank">• Michael Page Portugal</a></td>
                                <td style="padding:4px 0;"><a href="https://www.pageexecutive.com/" style="color:#0284c7;text-decoration:none;font-weight:bold;" target="_blank">• Page Executive (C-Level)</a></td>
                            </tr>
                            <tr>
                                <td style="padding:4px 0;"><a href="https://www.hays.pt/" style="color:#0284c7;text-decoration:none;font-weight:bold;" target="_blank">• Hays Portugal (Executivo)</a></td>
                                <td style="padding:4px 0;"><a href="https://www.stantonchase.com/office/executive-search-firm-in-lisbon-portugal" style="color:#0284c7;text-decoration:none;font-weight:bold;" target="_blank">• Stanton Chase Lisboa</a></td>
                            </tr>
                            <tr>
                                <td style="padding:4px 0;"><a href="https://www.robertwalters.pt/" style="color:#0284c7;text-decoration:none;font-weight:bold;" target="_blank">• Robert Walters Portugal</a></td>
                                <td style="padding:4px 0;"><a href="https://www.getthejob.pt/" style="color:#0284c7;text-decoration:none;font-weight:bold;" target="_blank">• GetTheJob (Outplacement)</a></td>
                            </tr>
                        </table>
                    </div>
                </div>

                <!-- Footer -->
                <div style="background:#0f172a;color:#94a3b8;padding:16px 24px;text-align:center;font-size:11px;border-top:1px solid #1e293b;">
                    <p style="margin:0 0 4px 0;">Encontra em anexo o ficheiro <strong>relatorio_vagas.html</strong> com o dashboard interativo completo.</p>
                    <p style="margin:0;color:#64748b;">Agente Autónomo de Emprego • Notificação Matinal das 09:00 • Sistema Antigravity</p>
                </div>
            </div>
        </body>
        </html>
        """
        return html

    def send_via_apple_mail(self, subject: str, text_content: str, attachment_path: Optional[str] = None) -> bool:
        """Envia e-mail através da aplicação nativa Apple Mail no macOS via osascript."""
        try:
            escaped_subject = subject.replace('\\', '\\\\').replace('"', '\\"')
            escaped_content = text_content.replace('\\', '\\\\').replace('"', '\\"')

            attachment_script = ""
            if attachment_path and Path(attachment_path).exists():
                abs_attach = str(Path(attachment_path).resolve())
                attachment_script = f"""
                set theAttachment to POSIX file "{abs_attach}"
                tell content
                    make new attachment with properties {{file name:theAttachment}} at after the last paragraph
                end tell
                """

            apple_script = f"""
            tell application "Mail"
                set msg to make new outgoing message with properties {{subject:"{escaped_subject}", content:"{escaped_content}", visible:false}}
                tell msg
                    set sender to "{self.sender}"
                    make new to recipient at end of to recipients with properties {{address:"{self.recipient}"}}
                    {attachment_script}
                    send
                end tell
            end tell
            """

            res = subprocess.run(["osascript", "-e", apple_script], capture_output=True, text=True)
            if res.returncode == 0:
                console.print(f"📧 [bold green]E-mail enviado com sucesso via Apple Mail para {self.recipient}![/bold green]")
                return True
            else:
                console.print(f"[yellow]⚠️ Falha no envio via Apple Mail: {res.stderr}[/yellow]")
                return False
        except Exception as e:
            console.print(f"[red]❌ Erro ao enviar por Apple Mail: {e}[/red]")
            return False

    def send_via_resend(self, subject: str, text_content: str, html_content: str, attachment_path: Optional[str] = None) -> bool:
        """Envia e-mail via API REST da Resend (HTTPS porta 443, 100% compatível com Render Free Tier)."""
        resend_key = os.environ.get("RESEND_API_KEY")
        if not resend_key:
            return False
        try:
            import base64
            import requests
            headers = {
                "Authorization": f"Bearer {resend_key.strip()}",
                "Content-Type": "application/json"
            }
            payload = {
                "from": "Agente Emprego <onboarding@resend.dev>",
                "to": [self.recipient],
                "subject": subject,
                "html": html_content,
                "text": text_content
            }
            if attachment_path and Path(attachment_path).exists():
                data_b64 = base64.b64encode(Path(attachment_path).read_bytes()).decode('utf-8')
                payload["attachments"] = [{
                    "filename": Path(attachment_path).name,
                    "content": data_b64
                }]
            resp = requests.post("https://api.resend.com/emails", json=payload, headers=headers, timeout=10.0)
            if resp.status_code in [200, 201]:
                console.print(f"📧 [bold green]E-mail enviado com sucesso via Resend API (HTTPS 443) para {self.recipient}![/bold green]")
                return True
            else:
                console.print(f"[yellow]⚠️ Resend API devolveu código {resp.status_code}: {resp.text}[/yellow]")
                return False
        except Exception as e:
            console.print(f"[yellow]⚠️ Erro na API Resend: {e}[/yellow]")
            return False

    def send_via_smtp(self, subject: str, text_content: str, html_content: str, attachment_path: Optional[str] = None) -> bool:
        """Envia e-mail via servidor SMTP (ex: Gmail SMTP) testando portas 465 (SSL) e 587 (TLS)."""
        try:
            if not self.smtp_password:
                return False

            clean_pwd = self.smtp_password.replace(" ", "").strip()
            msg = MIMEMultipart("mixed")
            msg["Subject"] = subject
            msg["From"] = self.sender
            msg["To"] = self.recipient

            alt_part = MIMEMultipart("alternative")
            alt_part.attach(MIMEText(text_content, "plain", "utf-8"))
            alt_part.attach(MIMEText(html_content, "html", "utf-8"))
            msg.attach(alt_part)

            if attachment_path and Path(attachment_path).exists():
                with open(attachment_path, "rb") as f:
                    part = MIMEApplication(f.read(), Name=Path(attachment_path).name)
                    part["Content-Disposition"] = f'attachment; filename="{Path(attachment_path).name}"'
                    msg.attach(part)

            # 1. Tentar porta 465 (SSL Direto)
            try:
                console.print(f"📧 A testar envio via SMTP SSL ({self.smtp_host}:465)...")
                with smtplib.SMTP_SSL(self.smtp_host, 465, timeout=4.0) as server:
                    server.login(self.smtp_user, clean_pwd)
                    server.sendmail(self.sender, [self.recipient], msg.as_string())
                console.print(f"📧 [bold green]E-mail enviado com sucesso via SMTP SSL (465) para {self.recipient}![/bold green]")
                return True
            except Exception as e_ssl:
                console.print(f"[dim]ℹ️ Porta 465 não disponível ({e_ssl}). A testar porta 587 TLS...[/dim]")

            # 2. Tentar porta 587 (STARTTLS)
            try:
                with smtplib.SMTP(self.smtp_host, 587, timeout=4.0) as server:
                    server.starttls()
                    server.login(self.smtp_user, clean_pwd)
                    server.sendmail(self.sender, [self.recipient], msg.as_string())
                console.print(f"📧 [bold green]E-mail enviado com sucesso via SMTP TLS (587) para {self.recipient}![/bold green]")
                return True
            except Exception as e_tls:
                console.print(f"[dim]ℹ️ Porta 587 não disponível ({e_tls}).[/dim]")

            return False
        except Exception as e:
            console.print(f"[yellow]⚠️ Falha na rotina SMTP: {e}[/yellow]")
            return False

    def send_daily_digest(self, profile: CVProfile, offers: List[JobOffer], html_report_path: Optional[str] = None, top_n: int = 10) -> bool:
        """
        Ponto de entrada principal para envio da notificação diária.
        1. SMTP seguro (porta 465 SSL ou 587 TLS com App Password)
        2. Resend API (se configurada)
        3. Apple Mail nativo (se estiver em macOS local)
        """
        now_date_str = datetime.now(LISBON_TZ).strftime("%d/%m/%Y")
        subject = f"🎯 Resumo Diário de Vagas Executivas (Lisboa & Remoto) - {profile.name} - {now_date_str}"
        
        text_body = self.build_text_body(profile, offers, top_n=top_n)
        html_body = self.build_html_body(profile, offers, top_n=top_n)

        # Salvar cópia local do corpo do e-mail para histórico e consulta web
        Path("email_digest_latest.html").write_text(html_body, encoding="utf-8")
        Path("email_digest_latest.txt").write_text(text_body, encoding="utf-8")

        # 1. Se credenciais SMTP estiverem presentes, tenta SMTP seguro
        if self.smtp_password:
            console.print("📧 A testar envio via servidor seguro da Google (Gmail)...")
            if self.send_via_smtp(subject, text_body, html_body, html_report_path):
                return True

        # 2. Se RESEND_API_KEY estiver configurada, tenta API HTTPS
        if os.environ.get("RESEND_API_KEY"):
            console.print("📧 A tentar envio via Resend API (HTTPS porta 443)...")
            if self.send_via_resend(subject, text_body, html_body, html_report_path):
                return True

        # 3. Em macOS (ambiente local), utilizar Apple Mail nativo
        import sys
        if sys.platform == "darwin":
            console.print("📧 A enviar notificação via Apple Mail nativo (macOS)...")
            if self.send_via_apple_mail(subject, text_body, html_report_path):
                return True
        else:
            console.print("[cyan]ℹ️ Resumo executivo guardado e disponível no dashboard web.[/cyan]")
            return False

        console.print("[bold yellow]ℹ️ Notificação gravada localmente com sucesso.[/bold yellow]")
        return False

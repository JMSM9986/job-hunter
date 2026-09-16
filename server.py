#!/usr/bin/env python3
import os
import sys
import json
import time
import subprocess
import threading
from datetime import datetime, timedelta
from pathlib import Path
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler

PORT = int(os.environ.get("PORT", 5050))
BASE_DIR = Path(__file__).resolve().parent

# Estado global da aplicação web
app_state = {
    "is_running": False,
    "last_run": None,
    "last_status": "Pronto para iniciar pesquisa",
    "total_offers": 0,
    "high_fit": 0,
    "part_time": 0,
    "remote": 0,
    "logs": [f"[{datetime.now().strftime('%H:%M:%S')}] Servidor de controlo web iniciado com sucesso."],
    "exit_code": 0
}
state_lock = threading.Lock()

def daily_scheduler_worker():
    """Agendador autónomo que dispara a pesquisa diária às 09:00 (hora local)."""
    while True:
        try:
            now = datetime.now()
            if now.hour == 9 and now.minute == 0:
                with state_lock:
                    running = app_state["is_running"]
                if not running:
                    add_log("⏰ Disparo automático matinal das 09:00 iniciado!")
                    t = threading.Thread(target=run_agent_pipeline, kwargs={"days": 15, "send_email": True}, daemon=True)
                    t.start()
                    time.sleep(70)
        except Exception as e:
            add_log(f"Erro no agendador diário: {e}")
        time.sleep(25)

def add_log(msg: str):
    with state_lock:
        timestamp = datetime.now().strftime("%H:%M:%S")
        app_state["logs"].append(f"[{timestamp}] {msg}")
        if len(app_state["logs"]) > 250:
            app_state["logs"] = app_state["logs"][-250:]

def update_stats_from_reports():
    """Lê relatorio_vagas.md ou ficheiros de dados para atualizar estatísticas."""
    md_path = BASE_DIR / "relatorio_vagas.md"
    if not md_path.exists():
        return
    try:
        content = md_path.read_text(encoding="utf-8")
        total = 0
        high = 0
        pt = 0
        rem = 0
        search_date = None
        for line in content.splitlines():
            clean = line.replace("*", "").strip().lstrip("-").strip()
            if "Data da Pesquisa:" in clean:
                search_date = clean.split("Data da Pesquisa:")[-1].strip()
            elif "Total de Ofertas Válidas:" in clean:
                total = int(clean.split(":")[-1].strip())
            elif "Ofertas com Elevada Compatibilidade" in clean:
                high = int(clean.split(":")[-1].strip())
            elif "Ofertas em Part-Time" in clean:
                pt = int(clean.split(":")[-1].strip())
            elif "Ofertas em Regime Remoto" in clean:
                rem = int(clean.split(":")[-1].strip())

        if not search_date:
            mod_time = datetime.fromtimestamp(md_path.stat().st_mtime)
            search_date = mod_time.strftime("%d/%m/%Y às %H:%M")

        with state_lock:
            app_state["total_offers"] = total
            app_state["high_fit"] = high
            app_state["part_time"] = pt
            app_state["remote"] = rem
            app_state["last_run"] = search_date
    except Exception as e:
        print(f"Erro ao ler estatísticas: {e}")

# Atualizar estatísticas iniciais
update_stats_from_reports()

def run_agent_pipeline(days: int = 15, send_email: bool = True, location: str = "Lisboa"):
    """Executa o pipeline em thread separada com captura de logs em tempo real."""
    with state_lock:
        app_state["is_running"] = True
        app_state["last_status"] = "A executar pesquisa nos portais..."
    
    add_log(f"🚀 Iniciando pesquisa: Janela={days} dias, Localização={location}, E-mail={send_email}")

    venv_python = BASE_DIR / ".venv" / "bin" / "python"
    python_bin = str(venv_python) if venv_python.exists() else sys.executable
    cmd = [
        python_bin,
        "-u",
        str(BASE_DIR / "main.py"),
        "--days", str(days),
        "--location", location
    ]
    if send_email:
        cmd.append("--email")
    else:
        cmd.append("--no-email")

    sub_env = os.environ.copy()
    sub_env["PYTHONUNBUFFERED"] = "1"

    try:
        process = subprocess.Popen(
            cmd,
            cwd=str(BASE_DIR),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            env=sub_env
        )

        for line in iter(process.stdout.readline, ''):
            clean_line = line.strip()
            if clean_line:
                add_log(clean_line)

        process.stdout.close()
        try:
            return_code = process.wait(timeout=150)
        except subprocess.TimeoutExpired:
            process.kill()
            return_code = -1
            add_log("⏱️ Limite de tempo excedido (150s). Processo interrompido com segurança.")

        update_stats_from_reports()

        with state_lock:
            app_state["is_running"] = False
            app_state["exit_code"] = return_code
            now_str = datetime.now().strftime("%d/%m/%Y às %H:%M")
            app_state["last_run"] = now_str
            if return_code == 0:
                app_state["last_status"] = f"Concluído com sucesso ({now_str})"
                add_log("✨ Pesquisa e processamento concluídos com sucesso!")
            else:
                app_state["last_status"] = f"Terminou com avisos/código {return_code}"
                add_log(f"⚠️ Processo concluído com código: {return_code}")

    except Exception as e:
        with state_lock:
            app_state["last_status"] = f"Erro na execução: {e}"
        add_log(f"❌ Erro fatal na execução: {e}")
    finally:
        with state_lock:
            app_state["is_running"] = False

class AgentWebHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Silenciar logs verbosos na consola
        pass

    def _send_bytes(self, data: bytes, content_type: str = "text/html; charset=utf-8", status: int = 200):
        """Envia resposta com suporte a compressão GZIP se suportada pelo cliente."""
        accept_encoding = self.headers.get("Accept-Encoding", "")
        if "gzip" in accept_encoding and len(data) > 300:
            import gzip
            compressed = gzip.compress(data)
            self.send_response(status)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Encoding', 'gzip')
            self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Expires', '0')
            self.send_header('Connection', 'close')
            self.send_header('Content-Length', str(len(compressed)))
            self.end_headers()
            self.wfile.write(compressed)
            self.wfile.flush()
        else:
            self.send_response(status)
            self.send_header('Content-Type', content_type)
            self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Expires', '0')
            self.send_header('Connection', 'close')
            self.send_header('Content-Length', str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            self.wfile.flush()

    def do_HEAD(self):
        parsed_path = self.path.split('?')[0]
        if parsed_path in ['/', '/index.html', '/dashboard']:
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
            self.end_headers()
        elif parsed_path == '/api/status':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
        elif parsed_path == '/favicon.ico':
            self.send_response(200)
            self.send_header('Content-Type', 'image/svg+xml')
            self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()

    def do_GET(self):
        parsed_path = self.path.split('?')[0]
        
        # Servir diretamente o Dashboard Interativo NATIVO (Zero Iframes)
        if parsed_path in ['/', '/index.html', '/dashboard']:
            report_file = BASE_DIR / "relatorio_vagas.html"
            if report_file.exists():
                content = report_file.read_bytes()
                self._send_bytes(content, content_type='text/html; charset=utf-8')
            else:
                self._send_bytes(b"<h1>Agente de Emprego ativo. A carregar dados...</h1>", status=200)

        elif parsed_path == '/api/status':
            pub_url = ""
            pub_file = BASE_DIR / "public_url.txt"
            if pub_file.exists():
                pub_url = pub_file.read_text().strip()
            with state_lock:
                copy_state = dict(app_state)
                copy_state["public_url"] = pub_url
                data = json.dumps(copy_state, ensure_ascii=False)
            
            self._send_bytes(data.encode('utf-8'), content_type='application/json; charset=utf-8')

        elif parsed_path == '/favicon.ico':
            # Ícone SVG embutido de alvo/briefcase
            icon_svg = b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><text y=".9em" font-size="90">&#127919;</text></svg>'
            self.send_response(200)
            self.send_header('Content-Type', 'image/svg+xml')
            self.send_header('Cache-Control', 'public, max-age=86400')
            self.send_header('Content-Length', str(len(icon_svg)))
            self.end_headers()
            self.wfile.write(icon_svg)

        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == '/api/run':
            with state_lock:
                if app_state["is_running"]:
                    self.send_response(409)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({"status": "already_running"}).encode('utf-8'))
                    return

            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length) if content_length > 0 else b'{}'
            try:
                params = json.loads(body.decode('utf-8'))
            except Exception:
                params = {}

            days = params.get('days', 15)
            send_email = params.get('send_email', True)

            t = threading.Thread(target=run_agent_pipeline, kwargs={"days": days, "send_email": send_email}, daemon=True)
            t.start()

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Connection', 'close')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "started"}).encode('utf-8'))
            self.wfile.flush()
        else:
            self.send_response(404)
            self.send_header('Connection', 'close')
            self.end_headers()

def main():
    # Iniciar agendador diário autónomo em background
    scheduler_thread = threading.Thread(target=daily_scheduler_worker, daemon=True)
    scheduler_thread.start()

    server = ThreadingHTTPServer(('0.0.0.0', PORT), AgentWebHandler)
    print(f"============================================================")
    print(f"🌐 Servidor Web Nativo do Agente de Emprego Ativo!")
    print(f"🔗 Local (Mac): http://localhost:{PORT}")
    print(f"📱 Telemóvel (Wi-Fi): http://192.168.1.245:{PORT}")
    print(f"⏰ Agendador Diário Autónomo das 09:00: ATIVO")
    print(f"============================================================")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nA encerrar servidor web...")
        server.server_close()

if __name__ == "__main__":
    main()

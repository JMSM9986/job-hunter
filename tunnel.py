#!/usr/bin/env python3
import re
import time
import subprocess
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
LOG_FILE = BASE_DIR / "tunnel.log"
URL_FILE = BASE_DIR / "public_url.txt"
CLOUDFLARED = BASE_DIR / "cloudflared"

def log(msg: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted = f"[{ts}] {msg}"
    print(formatted, flush=True)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(formatted + "\n")
    except Exception:
        pass

def run_tunnel():
    while True:
        log("🚀 A iniciar novo túnel público Cloudflare...")
        if URL_FILE.exists():
            try:
                URL_FILE.unlink()
            except Exception:
                pass

        cmd = [str(CLOUDFLARED), "tunnel", "--url", "http://127.0.0.1:5050", "--no-autoupdate"]
        proc = None
        try:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )

            for line in iter(proc.stdout.readline, ''):
                line_clean = line.strip()
                if not line_clean:
                    continue
                try:
                    with open(LOG_FILE, "a", encoding="utf-8") as f:
                        f.write(line_clean + "\n")
                except Exception:
                    pass

                match = re.search(r'(https://[a-zA-Z0-9-]+\.trycloudflare\.com)', line_clean)
                if match and "api.trycloudflare.com" not in match.group(1):
                    url = match.group(1)
                    URL_FILE.write_text(url, encoding="utf-8")
                    log("==========================================================")
                    log(f"🌍 NOVO LINK ATIVO: {url}")
                    log(f"📱 ACEDA NO TELEMÓVEL: {url}")
                    log("==========================================================")

                if "Unauthorized: Tunnel not found" in line_clean:
                    log("⚠️ Sessão expirada na Cloudflare (Mac suspenso/reativado). A forçar reinício...")
                    proc.terminate()
                    break

            proc.stdout.close()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()

        except Exception as e:
            log(f"⚠️ Erro no túnel: {e}")
            if proc:
                try:
                    proc.kill()
                except Exception:
                    pass

        log("Aguardando 3 segundos para restabelecer ligação...")
        time.sleep(3)

if __name__ == "__main__":
    run_tunnel()

#!/usr/bin/env bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

PORT=5050

# Iniciar servidor web se não estiver ativo
if ! lsof -i :$PORT >/dev/null 2>&1; then
    echo "A iniciar servidor web local..."
    .venv/bin/python server.py &
    sleep 1
fi

# Iniciar túnel Cloudflare para telemóvel se não estiver ativo
if ! pgrep -f "cloudflared tunnel" >/dev/null 2>&1; then
    echo "A iniciar túnel Cloudflare seguro para telemóvel..."
    ./tunnel.sh &
    sleep 2
fi

PUB_URL=$(cat public_url.txt 2>/dev/null || echo "")

echo "=========================================================="
echo "🚀 CENTRO DE CONTROLO WEB ATIVO COM SUCESSO!"
echo "💻 No Mac (Edge, Chrome, Safari): http://localhost:$PORT"
echo "📱 No Telemóvel (Na mesma rede Wi-Fi): http://192.168.1.245:$PORT"
if [ -n "$PUB_URL" ]; then
    echo "🌍 No Telemóvel (De qualquer lugar / 4G / 5G): $PUB_URL"
fi
echo "=========================================================="

open "http://localhost:$PORT"

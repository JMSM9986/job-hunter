#!/usr/bin/env bash
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

if [ ! -d ".venv" ]; then
    echo "A criar ambiente virtual..."
    python3 -m venv .venv
    .venv/bin/pip install -r requirements.txt
fi

echo "=========================================================="
echo "🎯 Agente de Procura de Emprego (Lisboa & Remoto)"
echo "=========================================================="

.venv/bin/python main.py "$@"

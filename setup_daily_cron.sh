#!/usr/bin/env bash
# Script para agendar a execução diária do Agente de Emprego às 09:00 no macOS
# Funciona mesmo com o Antigravity fechado através do crontab do utilizador macOS

AGENT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
RUN_SCRIPT="$AGENT_DIR/run.sh"

CRON_JOB="0 9 * * * cd $AGENT_DIR && ./run.sh >> $AGENT_DIR/daily_execution.log 2>&1"

# Verificar se já existe no crontab
( crontab -l 2>/dev/null | grep -v "$RUN_SCRIPT" ; echo "$CRON_JOB" ) | crontab -

echo "=========================================================="
echo "✅ Agendamento diário instalado com sucesso no macOS!"
echo "⏰ Horário: Todos os dias às 09:00 da manhã"
echo "📬 Destinatário: jmsmonteiro@gmail.com"
echo "📁 Diretório: $AGENT_DIR"
echo "📋 Log de execuções: $AGENT_DIR/daily_execution.log"
echo "=========================================================="

#!/bin/bash
"""
Script de configuração para limpeza automática de logs

Este script configura a limpeza automática de logs para ser executada periodicamente.
"""

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
CLEANUP_SCRIPT="$SCRIPT_DIR/cleanup_logs.py"

echo "🧹 Configurando limpeza automática de logs..."
echo "📂 Projeto: $PROJECT_ROOT"

# Verificar se o script existe
if [ ! -f "$CLEANUP_SCRIPT" ]; then
    echo "❌ Script de limpeza não encontrado: $CLEANUP_SCRIPT"
    exit 1
fi

# Tornar o script executável
chmod +x "$CLEANUP_SCRIPT"

echo "✅ Script de limpeza configurado"
echo ""
echo "🔧 Opções de execução:"
echo ""
echo "1. Manual:"
echo "   python $CLEANUP_SCRIPT"
echo ""
echo "2. Com parâmetros:"
echo "   python $CLEANUP_SCRIPT --max-age 3 --max-size 50"
echo ""
echo "3. Apenas estatísticas:"
echo "   python $CLEANUP_SCRIPT --stats-only"
echo ""
echo "4. Configurar cron job (Linux/Mac):"
echo "   crontab -e"
echo "   # Adicionar linha para executar diariamente às 02:00:"
echo "   0 2 * * * cd $PROJECT_ROOT && python $CLEANUP_SCRIPT > /dev/null 2>&1"
echo ""
echo "5. Configurar Task Scheduler (Windows):"
echo "   schtasks /create /tn \"SystemRAG_LogCleanup\" /tr \"python $CLEANUP_SCRIPT\" /sc daily /st 02:00"
echo ""

# Executar limpeza inicial para testar
echo "🧪 Executando limpeza de teste..."
python "$CLEANUP_SCRIPT" --stats-only

echo ""
echo "✅ Configuração concluída!"
echo "💡 Execute 'python $CLEANUP_SCRIPT --help' para ver todas as opções"
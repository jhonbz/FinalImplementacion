#!/bin/bash
set -e

echo "🚀 Iniciando Café de Magga — Agente Inteligente"

# ── Iniciar Ollama en segundo plano ──────────────────────────────
echo "⏳ Iniciando servidor Ollama..."
ollama serve &
OLLAMA_PID=$!

# Esperar a que Ollama esté listo
echo "⏳ Esperando que Ollama esté disponible..."
for i in {1..30}; do
    if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        echo "✅ Ollama listo"
        break
    fi
    sleep 2
done

# ── Descargar modelos si no existen ─────────────────────────────
echo "⏳ Verificando modelo LLM (llama3.2)..."
if ! ollama list | grep -q "llama3.2"; then
    echo "📥 Descargando llama3.2 (primera vez, puede tardar)..."
    ollama pull llama3.2
    echo "✅ llama3.2 descargado"
else
    echo "✅ llama3.2 ya disponible"
fi

# ── Crear directorios necesarios ─────────────────────────────────
mkdir -p /app/chroma_db /app/uploads

# ── Iniciar FastAPI ──────────────────────────────────────────────
echo "🌐 Iniciando API en puerto 8000..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000

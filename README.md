# ☕ Café de Magga — Asistente Virtual con RAG

Agente inteligente construido con **LangChain**, **LangGraph** y **RAG** para responder preguntas sobre las recetas y procedimientos del Café de Magga.

## 🏗️ Arquitectura

```
Usuario → React Frontend → FastAPI Backend → Agente LangGraph
                                                  ↓
                                           ChromaDB (búsqueda vectorial)
                                                  ↓
                                        Ollama + Llama 3.1 (modelo local)
```

## 🚀 Ejecutar localmente

### Prerequisitos
- Python 3.11+
- Node.js 18+
- [Ollama](https://ollama.com) instalado y corriendo

### 1. Descargar modelos en Ollama
```bash
ollama pull llama3.1
ollama pull nomic-embed-text
```

### 2. Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

### 3. Frontend
```bash
cd frontend
npm install --cache /tmp/npm-cache
npm run dev
```

Abre: http://localhost:5173

## 🔑 Variables de entorno

Ver `backend/.env.example`

## 📁 Estructura del proyecto

```
├── backend/
│   ├── app/
│   │   ├── agents/graph.py          # Agente LangGraph (6 nodos)
│   │   ├── controllers/             # Endpoints REST
│   │   ├── core/                    # Config y seguridad JWT
│   │   ├── models/                  # SQLite: usuarios, historial, documentos
│   │   ├── services/                # Procesamiento de documentos
│   │   └── vectorstore/             # ChromaDB
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── pages/                   # Login, Register, Chat, Docs
│       ├── components/              # Layout con sidebar
│       ├── context/                 # AuthContext (JWT)
│       └── services/api.js          # Axios con interceptores
└── docker-compose.yml
```

## 🤖 Flujo del agente LangGraph

1. **recibir_pregunta** — Limpia y prepara la pregunta
2. **buscar_contexto** — Busca en ChromaDB (umbral de similitud 0.4)
3. **validar_relevancia** — ¿Hay contexto suficiente?
4. **generar_respuesta** — LLM genera respuesta con el contexto
5. **sin_informacion** — Responde "No tengo información" si no hay contexto
6. **guardar_historial** — Guarda la interacción en SQLite

## 🛡️ Anti-alucinaciones

- Umbral mínimo de similitud en ChromaDB (score ≥ 0.4)
- Nodo de validación antes de responder
- Prompt explícito que prohíbe inventar información

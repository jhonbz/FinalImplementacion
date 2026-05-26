"""
Agente LangGraph para el Café de Magga.

Flujo del grafo:
  recibir_pregunta
       ↓
  expandir_query          ← NUEVO: genera keywords para mejor búsqueda
       ↓
  buscar_contexto
       ↓
  validar_relevancia ──► sin_informacion (END)
       ↓
  generar_respuesta
       ↓
  guardar_historial (END)
"""

from typing import TypedDict
from langgraph.graph import StateGraph, END
from langchain_ollama import OllamaLLM
from app.vectorstore.chroma_store import search_similar
from app.core.config import settings


# ─────────────────────────────────────────
# Estado del agente
# ─────────────────────────────────────────
class AgentState(TypedDict):
    question: str
    search_query: str        # Query expandida para búsqueda en ChromaDB
    context: list[dict]
    answer: str
    sources: list[str]
    has_context: bool
    user_id: int


# ─────────────────────────────────────────
# LLM local
# ─────────────────────────────────────────
def get_llm() -> OllamaLLM:
    return OllamaLLM(
        base_url=settings.OLLAMA_BASE_URL,
        model=settings.OLLAMA_MODEL,
        temperature=0.0,
        num_predict=600,
    )


# ─────────────────────────────────────────
# NODO 1: Recibir pregunta
# ─────────────────────────────────────────
def nodo_recibir_pregunta(state: AgentState) -> AgentState:
    return {
        **state,
        "question": state["question"].strip(),
        "search_query": state["question"].strip(),
        "context": [],
        "answer": "",
        "sources": [],
        "has_context": False,
    }


# ─────────────────────────────────────────
# NODO 1.5: Expandir query para mejor búsqueda
# ─────────────────────────────────────────
def nodo_expandir_query(state: AgentState) -> AgentState:
    """
    Extrae términos clave de la pregunta para mejor búsqueda en ChromaDB.
    Usa prompt directo (string) para compatibilidad con llama3.2.
    """
    llm = get_llm()
    prompt_str = (
        f"Extrae 5 palabras clave de esta pregunta sobre un café. "
        f"Solo las palabras, separadas por comas.\n"
        f"Pregunta: {state['question']}\nPalabras clave:"
    )
    try:
        keywords = llm.invoke(prompt_str).strip().split("\n")[0]
        search_query = f"{state['question']} {keywords}"
    except Exception:
        search_query = state["question"]

    return {**state, "search_query": search_query}


# ─────────────────────────────────────────
# NODO 2: Buscar contexto en ChromaDB
# ─────────────────────────────────────────
def nodo_buscar_contexto(state: AgentState) -> AgentState:
    """
    Recupera fragmentos usando la query expandida.
    Anti-alucinación #1: umbral mínimo de similitud.
    """
    resultados = search_similar(
        query=state["question"],
        k=8,
        score_threshold=0.2,
    )

    contexto, fuentes = [], []
    for doc, score in resultados:
        contexto.append({
            "content": doc.page_content,
            "source": doc.metadata.get("source", "Documento"),
            "score": round(score, 3),
        })
        src = doc.metadata.get("source", "Documento")
        if src not in fuentes:
            fuentes.append(src)

    return {**state, "context": contexto, "sources": fuentes}


# ─────────────────────────────────────────
# NODO 3: Validar relevancia
# ─────────────────────────────────────────
def nodo_validar_relevancia(state: AgentState) -> AgentState:
    """Anti-alucinación #2: verificar contexto antes de responder."""
    return {**state, "has_context": len(state["context"]) > 0}


def ruta_validacion(state: AgentState) -> str:
    return "generar_respuesta" if state["has_context"] else "sin_informacion"


# ─────────────────────────────────────────
# NODO 4: Generar respuesta
# ─────────────────────────────────────────
def nodo_generar_respuesta(state: AgentState) -> AgentState:
    """
    Anti-alucinación #3: prompt directo que obliga a usar solo el contexto.
    Usa string format directo (compatible con modelos pequeños como llama3.2).
    """
    llm = get_llm()

    contexto_texto = "\n---\n".join([item["content"] for item in state["context"]])

    # Prompt como string directo — más confiable con modelos pequeños
    prompt_str = (
        f"Eres el asistente del Café de Magga. "
        f"Responde en español usando SOLO la información del contexto.\n\n"
        f"CONTEXTO:\n{contexto_texto}\n\n"
        f"PREGUNTA: {state['question']}\n\n"
        f"RESPUESTA (solo con info del contexto):"
    )

    respuesta = llm.invoke(prompt_str)
    return {**state, "answer": respuesta.strip()}


# ─────────────────────────────────────────
# NODO 5: Sin información
# ─────────────────────────────────────────
def nodo_sin_informacion(state: AgentState) -> AgentState:
    return {
        **state,
        "answer": (
            "No tengo suficiente información en mi base de conocimiento para "
            "responder esa pregunta. Te sugiero subir documentos relacionados "
            "con el tema desde el panel de Documentos."
        ),
        "sources": [],
    }


# ─────────────────────────────────────────
# NODO 6: Guardar historial
# ─────────────────────────────────────────
def nodo_guardar_historial(state: AgentState) -> AgentState:
    return state


# ─────────────────────────────────────────
# CONSTRUCCIÓN DEL GRAFO
# ─────────────────────────────────────────
def build_agent_graph():
    graph = StateGraph(AgentState)

    graph.add_node("recibir_pregunta",   nodo_recibir_pregunta)
    graph.add_node("expandir_query",     nodo_expandir_query)
    graph.add_node("buscar_contexto",    nodo_buscar_contexto)
    graph.add_node("validar_relevancia", nodo_validar_relevancia)
    graph.add_node("generar_respuesta",  nodo_generar_respuesta)
    graph.add_node("sin_informacion",    nodo_sin_informacion)
    graph.add_node("guardar_historial",  nodo_guardar_historial)

    graph.set_entry_point("recibir_pregunta")
    graph.add_edge("recibir_pregunta",   "buscar_contexto")
    graph.add_edge("buscar_contexto",    "validar_relevancia")
    graph.add_conditional_edges(
        "validar_relevancia",
        ruta_validacion,
        {
            "generar_respuesta": "generar_respuesta",
            "sin_informacion":   "sin_informacion",
        },
    )
    graph.add_edge("generar_respuesta",  "guardar_historial")
    graph.add_edge("sin_informacion",    "guardar_historial")
    graph.add_edge("guardar_historial",  END)

    return graph.compile()


agent_graph = build_agent_graph()


async def run_agent(question: str, user_id: int) -> dict:
    initial_state = AgentState(
        question=question,
        search_query=question,
        context=[],
        answer="",
        sources=[],
        has_context=False,
        user_id=user_id,
    )
    final_state = agent_graph.invoke(initial_state)
    return {
        "answer":       final_state["answer"],
        "sources":      final_state["sources"],
        "has_context":  final_state["has_context"],
        "context_used": final_state["context"],
    }

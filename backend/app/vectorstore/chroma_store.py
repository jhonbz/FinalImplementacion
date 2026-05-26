import chromadb
from chromadb.config import Settings as ChromaSettings
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings
from app.core.config import settings

_chroma_client = None
_vectorstore = None

# Modelo de embeddings vía Ollama — no requiere PyTorch
EMBEDDING_MODEL = "nomic-embed-text"


def get_chroma_client() -> chromadb.Client:
    global _chroma_client
    if _chroma_client is None:
        _chroma_client = chromadb.PersistentClient(
            path=settings.CHROMA_PERSIST_DIR,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
    return _chroma_client


def get_vectorstore() -> Chroma:
    global _vectorstore
    if _vectorstore is None:
        embeddings = OllamaEmbeddings(
            model=EMBEDDING_MODEL,
            base_url=settings.OLLAMA_BASE_URL,
        )
        _vectorstore = Chroma(
            client=get_chroma_client(),
            collection_name=settings.CHROMA_COLLECTION,
            embedding_function=embeddings,
            collection_metadata={"hnsw:space": "cosine"},
        )
    return _vectorstore


def search_similar(query: str, k: int = 5, score_threshold: float = 0.3):
    """
    Busca fragmentos usando similitud coseno con embeddings multilingüe.
    Anti-alucinación #1: umbral mínimo de relevancia.
    """
    store = get_vectorstore()
    results = store.similarity_search_with_relevance_scores(query, k=k)
    return [(doc, score) for doc, score in results if score >= score_threshold]


def add_texts_to_store(texts: list[str], metadatas: list[dict]) -> int:
    store = get_vectorstore()
    store.add_texts(texts=texts, metadatas=metadatas)
    return len(texts)


def delete_document_chunks(filename: str):
    client = get_chroma_client()
    try:
        collection = client.get_collection(settings.CHROMA_COLLECTION)
        collection.delete(where={"source": filename})
    except Exception:
        pass

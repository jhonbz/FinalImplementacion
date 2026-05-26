"""
Servicio para procesar documentos y cargarlos en ChromaDB.
Soporta: PDF, TXT, Markdown, DOCX, CSV
"""
import os
import uuid
from pathlib import Path
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import (
    PyPDFLoader,
    TextLoader,
    Docx2txtLoader,
    CSVLoader,
)
from app.vectorstore.chroma_store import add_texts_to_store, delete_document_chunks
from app.core.config import settings


ALLOWED_EXTENSIONS = {".pdf", ".txt", ".md", ".docx", ".csv"}

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=900,          # Fragmentos más grandes para mantener secciones completas
    chunk_overlap=100,       # Solapamiento para no perder contexto entre fragmentos
    separators=["\n\n", "\n", ". ", " ", ""],
)


def get_loader(file_path: str, extension: str):
    """Retorna el loader apropiado según la extensión del archivo."""
    loaders = {
        ".pdf": PyPDFLoader,
        ".txt": TextLoader,
        ".md": TextLoader,
        ".docx": Docx2txtLoader,
        ".csv": CSVLoader,
    }
    loader_class = loaders.get(extension)
    if not loader_class:
        raise ValueError(f"Formato no soportado: {extension}")

    if extension == ".txt" or extension == ".md":
        return loader_class(file_path, encoding="utf-8")
    return loader_class(file_path)


async def process_document(file_path: str, original_name: str) -> dict:
    """
    Procesa un documento:
    1. Extrae el texto
    2. Divide en fragmentos
    3. Guarda embeddings en ChromaDB
    Retorna info del procesamiento.
    """
    extension = Path(original_name).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise ValueError(f"Formato no permitido. Use: {', '.join(ALLOWED_EXTENSIONS)}")

    # 1. Cargar y extraer texto
    loader = get_loader(file_path, extension)
    documents = loader.load()

    if not documents:
        raise ValueError("El documento está vacío o no se pudo leer.")

    # 2. Dividir en fragmentos
    chunks = text_splitter.split_documents(documents)

    if not chunks:
        raise ValueError("No se pudieron extraer fragmentos del documento.")

    # 3. Preparar textos y metadatos
    texts = [chunk.page_content for chunk in chunks]
    metadatas = [
        {
            "source": original_name,
            "page": chunk.metadata.get("page", 0),
            "chunk_index": i,
        }
        for i, chunk in enumerate(chunks)
    ]

    # 4. Guardar en ChromaDB
    count = add_texts_to_store(texts, metadatas)

    return {
        "original_name": original_name,
        "chunks_created": count,
        "pages_processed": len(documents),
    }


def save_uploaded_file(file_content: bytes, original_name: str) -> str:
    """Guarda el archivo en disco y retorna la ruta."""
    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(exist_ok=True)

    extension = Path(original_name).suffix.lower()
    unique_name = f"{uuid.uuid4().hex}{extension}"
    file_path = upload_dir / unique_name

    with open(file_path, "wb") as f:
        f.write(file_content)

    return str(file_path)


def remove_document(file_path: str, original_name: str):
    """Elimina el archivo físico y sus chunks de ChromaDB."""
    # Eliminar de ChromaDB
    delete_document_chunks(original_name)

    # Eliminar archivo físico
    if os.path.exists(file_path):
        os.remove(file_path)

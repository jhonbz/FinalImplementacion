from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.database import Document, get_db
from app.core.security import get_current_user
from app.services.document_service import (
    save_uploaded_file,
    process_document,
    remove_document,
    ALLOWED_EXTENSIONS,
)
from pathlib import Path

router = APIRouter(prefix="/documents", tags=["Documentos"])

MAX_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Validar extensión
    extension = Path(file.filename).suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Formato no permitido. Usa: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    # Leer contenido y validar tamaño
    content = await file.read()
    if len(content) > MAX_SIZE_BYTES:
        raise HTTPException(status_code=400, detail="El archivo supera los 10 MB.")

    user_id = int(current_user["sub"])

    # Registrar en BD como "processing"
    doc = Document(
        user_id=user_id,
        filename="",
        original_name=file.filename,
        file_type=extension,
        status="processing",
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)

    try:
        # Guardar archivo en disco
        file_path = save_uploaded_file(content, file.filename)

        # Procesar e indexar en ChromaDB
        result = await process_document(file_path, file.filename)

        # Actualizar registro
        doc.filename = file_path
        doc.chunk_count = result["chunks_created"]
        doc.status = "ready"
        await db.commit()

        return {
            "message": f"Documento procesado exitosamente.",
            "document_id": doc.id,
            "original_name": file.filename,
            "chunks_created": result["chunks_created"],
            "pages_processed": result["pages_processed"],
        }

    except Exception as e:
        doc.status = "error"
        await db.commit()
        raise HTTPException(status_code=500, detail=f"Error procesando el documento: {str(e)}")


@router.get("/")
async def list_documents(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user_id = int(current_user["sub"])
    result = await db.execute(
        select(Document).where(Document.user_id == user_id).order_by(Document.created_at.desc())
    )
    docs = result.scalars().all()

    return [
        {
            "id": d.id,
            "original_name": d.original_name,
            "file_type": d.file_type,
            "chunk_count": d.chunk_count,
            "status": d.status,
            "created_at": d.created_at.isoformat(),
        }
        for d in docs
    ]


@router.delete("/{document_id}")
async def delete_document(
    document_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user_id = int(current_user["sub"])
    result = await db.execute(
        select(Document).where(Document.id == document_id, Document.user_id == user_id)
    )
    doc = result.scalar_one_or_none()

    if not doc:
        raise HTTPException(status_code=404, detail="Documento no encontrado.")

    remove_document(doc.filename, doc.original_name)
    await db.delete(doc)
    await db.commit()

    return {"message": f"Documento '{doc.original_name}' eliminado correctamente."}

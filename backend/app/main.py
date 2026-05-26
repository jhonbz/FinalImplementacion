from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.models.database import init_db
from app.controllers.auth_controller import router as auth_router
from app.controllers.chat_controller import router as chat_router
from app.controllers.documents_controller import router as documents_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Al iniciar: crear tablas en la BD
    await init_db()
    print("✅ Base de datos inicializada")
    yield
    print("🛑 Servidor detenido")


app = FastAPI(
    title="Café de Magga — Agente Inteligente",
    description="API para el asistente virtual del Café de Magga con RAG",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — permite que el frontend React se comunique con el backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registrar routers
app.include_router(auth_router, prefix="/api")
app.include_router(chat_router, prefix="/api")
app.include_router(documents_router, prefix="/api")


@app.get("/")
async def root():
    return {
        "message": "☕ Bienvenido al Agente del Café de Magga",
        "docs": "/docs",
        "status": "running"
    }


@app.get("/health")
async def health():
    return {"status": "ok"}

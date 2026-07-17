from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.models.database import init_db
from app.routers import documents, selections, generation


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title="CT-200 Document Parser & QA Generator API",
    description="Parse CT-200 manuals into structured trees, version them, and generate QA test cases",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(documents.router)
app.include_router(selections.router)
app.include_router(generation.router)


@app.get("/")
async def root():
    return {
        "name": "CT-200 Document API",
        "version": "1.0.0",
        "endpoints": {
            "documents": "/api/documents",
            "ingest": "/api/documents/ingest?pdf_path=...&description=...",
            "sections": "/api/versions/{id}/sections",
            "node": "/api/nodes/{id}",
            "search": "/api/nodes/search?q=...",
            "diff": "/api/versions/{v1}/diff/{v2}",
            "selections": "/api/selections",
            "generate": "/api/generate",
            "generations": "/api/generations/{id}",
        },
    }

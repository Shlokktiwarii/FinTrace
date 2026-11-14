from contextlib import asynccontextmanager
from fintrace.api.routes.documents import router as documents_router
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fintrace.api.dependencies import initialize_services
from fintrace.api.routes import health, query
from fintrace.core.config import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()

    print("Initializing FinTrace services...")

    app.state.services = initialize_services(settings)

    print("FinTrace initialization completed.")

    yield

    vector_store = app.state.services["vector_store"]
    vector_store.client.close()

    print("FinTrace shutdown completed.")


app = FastAPI(
    title="FinTrace API",
    description="Evidence-first financial research and verification API.",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(
    health.router,
    prefix="/api/v1",
    tags=["Health"],
)

app.include_router(
    query.router,
    prefix="/api/v1",
    tags=["Financial Research"],
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(
    documents_router,
    prefix="/api/v1",
)


@app.get("/")
def root():
    return {
        "name": "FinTrace",
        "message": "Evidence-first financial research API",
        "docs": "/docs",
    }
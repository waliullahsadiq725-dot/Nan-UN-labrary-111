from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .database import Base, engine
from . import models
from .routers import auth, documents, admin

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.app_name,
    description="د ننګرهار پوهنتون ډیجیټل کتابتون لپاره REST API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(auth.router)
app.include_router(documents.router)
app.include_router(admin.router)

@app.get("/", tags=["System"])
def root():
    return {"name": settings.app_name, "status": "running", "docs": "/docs"}

@app.get("/api/health", tags=["System"])
def health():
    return {"status": "ok"}

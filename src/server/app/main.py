from fastapi import FastAPI
from .routers import nodes, metrics, alerts, auth
from .database import engine, Base
from config.settings import settings
from app.init_data import create_admin

# Créer les tables
Base.metadata.create_all(bind=engine)

#Créer l'admin automatiquement
create_admin()

app = FastAPI(
    title="Monitoring Distribué",
    version="1.0.0"
)

app.include_router(auth.router)
app.include_router(nodes.router)
app.include_router(metrics.router)
app.include_router(alerts.router)

@app.get("/health")
async def health():
    return {"status": "ok", "env": settings.ENV}

@app.get("/")
async def root():
    return {
        "message": "Monitoring Distribué API",
        "docs": "/docs",
        "health": "/health"
    }
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api.routes import router

app = FastAPI(
    title="World Cup 2026 Predictor",
    description="API de predicción de partidos y cálculos de parlays para el Mundial 2026",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1")

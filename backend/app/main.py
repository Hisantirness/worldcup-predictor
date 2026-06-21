from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api.routes import router
from .data_collector.collector import build_finished_games_cache, get_all_teams


@asynccontextmanager
async def lifespan(_app: FastAPI):
    await get_all_teams()
    await build_finished_games_cache()
    yield

app = FastAPI(
    title="World Cup 2026 Predictor",
    description="API de predicción de partidos y cálculos de parlays para el Mundial 2026",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1")

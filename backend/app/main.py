from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from .api.routes import router
from .data_collector.api_client import set_api_key
from .config import FOOTBALL_DATA_KEY

if FOOTBALL_DATA_KEY:
    set_api_key(FOOTBALL_DATA_KEY)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    yield

app = FastAPI(
    title="World Cup 2026 Predictor",
    description="API de predicción de partidos y cálculos de parlays para el Mundial 2026",
    version="1.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_frontend_dir = Path(__file__).resolve().parent.parent.parent / "frontend"

app.include_router(router, prefix="/api/v1")

if _frontend_dir.exists():
    app.mount("/css", StaticFiles(directory=str(_frontend_dir / "css")), name="css")
    app.mount("/js", StaticFiles(directory=str(_frontend_dir / "js")), name="js")

    @app.get("/")
    async def root():
        return FileResponse(_frontend_dir / "index.html")

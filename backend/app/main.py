from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api.routes import router
from .data_collector.collector import get_matches
from .models.calibration import evaluate_on_finished_matches, calibrate_weights
from .models.ensemble import set_weights, get_weights
from .models.elo import elo


@asynccontextmanager
async def lifespan(_app: FastAPI):
    matches = await get_matches()
    finished = [m for m in matches if m.get("status") == "finished" and m.get("score")]
    if finished:
        for m in finished:
            s = m["score"]
            elo.update_rating(m["home"], m["away"], s["home"], s["away"])
            elo.update_rating(m["away"], m["home"], s["away"], s["home"])
        evaluation = evaluate_on_finished_matches(finished)
        new_weights = calibrate_weights(evaluation)
        set_weights(new_weights)
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

app.include_router(router, prefix="/api/v1")

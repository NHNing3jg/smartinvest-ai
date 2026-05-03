from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes_backtest import router as backtest_router
from app.api.routes_health import router as health_router
from app.api.routes_portfolio import router as portfolio_router
from app.api.routes_recommendations import router as recommendations_router


app = FastAPI(title="SmartInvest AI API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, prefix="/api")
app.include_router(recommendations_router, prefix="/api")
app.include_router(backtest_router, prefix="/api")
app.include_router(portfolio_router, prefix="/api")

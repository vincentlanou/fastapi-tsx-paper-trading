from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from app.db.database import engine, Base
from app.routers import market, sentiment, trading, notifications, autopilot

# Create database tables if they do not exist
Base.metadata.create_all(bind=engine)

# Auto-migration for Phase 6: Add peak_price to Position table if missing
try:
    with engine.connect() as conn:
        conn.execute("ALTER TABLE positions ADD COLUMN peak_price FLOAT NOT NULL DEFAULT 0.0")
except Exception:
    pass # Column likely already exists

app = FastAPI(
    title="Trading Momentum & AI Sentiment Analytics Platform",
    description="FastAPI Paper Trading engine with yfinance RSI/MACD indicators, Gemini AI news sentiment analysis & Telegram webhooks.",
    version="1.0.0"
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(market.router)
app.include_router(sentiment.router)
app.include_router(trading.router)
app.include_router(notifications.router)
app.include_router(autopilot.router)

# Mount Static Files (Frontend UI Dashboard)
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

    @app.get("/", include_in_schema=False)
    def read_root():
        index_file = os.path.join(static_dir, "index.html")
        if os.path.exists(index_file):
            return FileResponse(index_file)
        return {"message": "FastAPI Trading Platform API is running. Access /docs for OpenAPI documentation."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)

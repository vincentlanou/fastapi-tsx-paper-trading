from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from app.db.database import engine, Base
from app.routers import market, sentiment, trading, notifications, autopilot

# Create database tables if they do not exist
Base.metadata.create_all(bind=engine)

from sqlalchemy import text, inspect

# Auto-migration: Add peak_price and created_at to Position table if missing (for legacy DBs)
# For NEW PostgreSQL databases, create_all() above already creates the full schema.
try:
    inspector = inspect(engine)
    existing_columns = [col["name"] for col in inspector.get_columns("positions")]
    with engine.connect() as conn:
        if "peak_price" not in existing_columns:
            conn.execute(text("ALTER TABLE positions ADD COLUMN peak_price FLOAT NOT NULL DEFAULT 0.0"))
            conn.commit()
        if "created_at" not in existing_columns:
            conn.execute(text("ALTER TABLE positions ADD COLUMN created_at TIMESTAMP"))
            conn.commit()
except Exception:
    pass  # Table may not exist yet (first run), create_all will handle it

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
